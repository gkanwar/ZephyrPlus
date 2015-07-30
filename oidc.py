import base64
import os
import simplejson
import urllib
import urlparse

import tornado
import tornado.concurrent
import tornado.httpclient
import tornado.httputil

class OidcMixin(object):
    _OIDC_AUTHORIZATION_ENDPOINT = None
    _OIDC_TOKEN_ENDPOINT = None
    _OIDC_USERINFO_ENDPOINT = None

    _OIDC_CLIENT_ID = None

    @tornado.concurrent.return_future
    def authorize_redirect(self, scope=None, callback=None):
        if scope is None:
            scope = ["openid", "email"]
        elif "openid" not in scope:
            scope = scope + ["openid"]

        state = self._gen_state()
        self.set_secure_cookie("oidc_state", state)

        args = {
            "redirect_uri": self._oidc_redirect_uri(),
            "client_id": self._OIDC_CLIENT_ID,
            "scope": " ".join(scope),
            "response_type": "code",
            "state": state
        }
        self.redirect(tornado.httputil.url_concat(
                self._OIDC_AUTHORIZATION_ENDPOINT, args))

        callback()

    def _oidc_redirect_uri(self):
        url = self.request.full_url()
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        query_dict = urlparse.parse_qs(query)
        clean_url = urlparse.urlunparse((scheme, netloc, path, params, "", ""))
        if "next" in query_dict:
            clean_url = tornado.httputil.url_concat(clean_url,
                                                    {"next": query_dict["next"][0]})
        return clean_url

    def _gen_state(self):
        return base64.b64encode(os.urandom(32), "\\/").replace("=", "~")

    @tornado.gen.coroutine
    def get_authenticated_user(self):
        code = self.get_argument("code", "")
        state = self.get_argument("state", "")
        cookie_state = self.get_secure_cookie("oidc_state")
        self.clear_cookie("oidc_state")
        if state != cookie_state:
            raise tornado.auth.AuthError("OIDC state incorrect")

        http = tornado.httpclient.AsyncHTTPClient()

        body = urllib.urlencode({
                "client_id": self._OIDC_CLIENT_ID,
                "grant_type": "authorization_code",
                "code": self.get_argument("code"),
                "redirect_uri": self._oidc_redirect_uri()
                })
        token_response = yield http.fetch(
            self._OIDC_TOKEN_ENDPOINT,
            method="POST",
            body=body)
        token = simplejson.loads(token_response.body)["access_token"]

        userinfo_response = yield http.fetch(
            self._OIDC_USERINFO_ENDPOINT,
            headers={"Authorization": "Bearer " + token},
            raise_error=False)
        if userinfo_response.code == 403 and \
                ("insufficient_scope" in userinfo_response.body or
                 "insufficient scope" in userinfo_response.body.lower()):
            raise tornado.auth.AuthError("OIDC insufficient scope")
        if userinfo_response.error:
            raise tornado.auth.AuthError(userinfo_response.error,
                                         userinfo_response.body)
        userinfo = simplejson.loads(userinfo_response.body)

        raise tornado.gen.Return(userinfo)
