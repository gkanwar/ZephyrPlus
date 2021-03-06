/*
 * ZephyrAPI -- Interface with server backend
 * 
 *      api = new ZephyrAPI(source)
 *              Create a new instance of the API and connect to server
 * 
 * Methods
 *      api.addSubscription(class, instance, recipient, callback)
 *      api.removeSubscription(class, instance, recipient, callback)
 *      api.sendZephyr({message, class, instance, recipient, signature}, callback)
 *      api.getClassById(id)
 *      api.getInstanceById(id)
 *      api.getMessageById(id)
 *      api.saveStorage(callback)
 *      api.getOldMessages(class, instance, recipient, startdate, callback)
 * 
 * Properties
 *      api.ready
 *              Boolean indicating whether or not the user's information has been retrieved from the server.
 *      api.classes
 *              Array of the classes that the user has subscribed to.  (See Google Docs for details)
 *      api.instances
 *              Array of instances that have zephyrs.  (See GDocs.)
 *      api.messages
 *              Array of all zephyrs that have been received.  (See GDocs.)
 *      api.username
 *              String containing the user's username.
 *      api.subscriptions
 *              Array of the user's subscriptions.
 *      api.storage
 *              Object on which data can be stored on the server
 *      api.status
 *              Integer indicating the status of the connection
 *              CONNECTED, CONNECTING, DISCONNECTED, UPDATESUGGESTED, UPDATEREQUIRED
 * 
 * Event handlers
 *      api.onready = function()
 *              Called when the API successfully retrives the user's information
 *              from the server, indicating that the API is ready to send and receive zephyrs.
 *      api.onzephyr = function(zephyrs)
 *              Called when zephyrs are received from the server.  zephyrs is an array of zephyrs.
 *      api.onerror = function(jqXHR, errorType)
 *              Called when an error occured while sending or retrieving information
 *              from the server.
 *      api.onstatuschange = function(newStatus)
 *              Called when the status of the connection changes
 */
(function(){
    function ZephyrAPI(source){
        var api = this;
        api.ready = false;
        api.classes = [];
        api.classDict = Object.create(null);
        api.instances = [];
        api.messages = [];
        api.last_messaged = new Date() - 3*24*60*60*1000;
        var classIdDict = Object.create(null);
        var instanceIdDict = Object.create(null);
        var messageIdDict = Object.create(null);
        
        api.status = ZephyrAPI.CONNECTING;
        var version;
        
        function procMessages(messages){
	    messages = messages.filter(function(m){
		return messageIdDict[m.id] == undefined;
	    });
            for(var n=0; n<messages.length; n++){
                messages[n] = {
                    id: messages[n].id,
                    parent_class: findClass(messages[n].class),
                    parent_instance: findInstance(messages[n].instance, messages[n].class),
                    sender: messages[n].sender,
                    timestamp: new Date(messages[n].date),
                    message_body: messages[n].message,
                    signature: messages[n].signature,
                    auth: messages[n].auth
                }
                if(messages[n].parent_class.last_messaged < messages[n].timestamp)
                    messages[n].parent_class.last_messaged = messages[n].timestamp;
                if(messages[n].parent_instance.last_messaged < messages[n].timestamp)
                    messages[n].parent_instance.last_messaged = messages[n].timestamp;
                if(api.last_messaged < messages[n].timestamp)
                    api.last_messaged = messages[n].timestamp;
                messages[n].parent_class.messages.push(messages[n]);
                messages[n].parent_instance.messages.push(messages[n]);
                if(messages[n].parent_class.name.indexOf("un") == 0
                        && messages[n].parent_class.name.length > 2){
                    findClass(messages[n].parent_class.name.substr(2)).messages.push(messages[n]);
                    findInstance(messages[n].parent_instance.name,
                                 messages[n].parent_class.name.substr(2)).messages.push(messages[n]);
                }
                api.messages.push(messages[n]);
                messageIdDict[messages[n].id] = messages[n];
            }
            if(api.onzephyr)
                api.onzephyr(messages);
        }
        
        function getOldMessages(sub, startdate, callback){
            if(startdate == undefined)
                startdate = new Date() - 1000*60*60*24*3;
            return source.getOldMessages(sub, startdate)
            .then(function(messages) {
                procMessages(messages);
                if (callback) {
                    return callback();
                }
            }, api.onerror);
        }
        
        function findClass(name){
            if(api.classDict[name] == undefined){
                api.classDict[name] = {
		    id: hashStringToNumber(name)+"",
                    name: name,
                    last_messaged: new Date(0),
                    color: hashStringToColor(name),
                    instances: [],
                    instanceDict: Object.create(null),
                    messages: [],
		    missedMessages: []
                }
                api.classes.push(api.classDict[name]);
                classIdDict[api.classDict[name].id] = api.classDict[name];
            }
            return api.classDict[name];
        }
        
        function findInstance(name, className){
            var parent = findClass(className);
            if(parent.instanceDict[name] == undefined){
                parent.instanceDict[name] = {
		    id: "instance"+hashStringToNumber(parent.id+"-_-"+name),
                    name: name,
                    last_messaged: new Date(0),
                    color: hashStringToColor(name),
                    parent_class: parent,
                    messages: [],
		    missedMessages: []
                }
                parent.instances.push(parent.instanceDict[name]);
                api.instances.push(parent.instanceDict[name]);
                instanceIdDict[parent.instanceDict[name].id] = parent.instanceDict[name];
            }
            return parent.instanceDict[name];
        }
        
        function setStatus(newStatus){
            if(newStatus != api.status){
                api.status = newStatus;
                if(api.onstatuschange)
                    api.onstatuschange(newStatus);
            }
        }
	source.onstatuschange = setStatus;
        
        function checkVersion(){
            $.get("/static/version", {"d": new Date()-0}, function(ver){
                ver = ver.split("\n")[0].split(".");
                if(version && ver[0] != version[0]){
                    setStatus(ZephyrAPI.UPDATE_REQUIRED);
                }
                else if(version && ver[1] != version[1]){
                    setStatus(ZephyrAPI.UPDATE_AVAILABLE);
                }
                version = ver;
            }, "text");
        }
        window.setInterval(checkVersion, 5*60*1000);
        
        source.init()
        .then(function(data) {
            api.username = data.username;
            api.subscriptions = data.subscriptions;
            api.storage = data.storage;
            for(var n=0; n<api.subscriptions.length; n++){
                findClass(api.subscriptions[n].class);
            }
            api.ready = true;
            if(api.onready)
                api.onready();
            source.onzephyr = procMessages;
            source.start();
            checkVersion();
        }, api.onerror);
        
        function checkReady(){
            if(!api.ready)
                throw new Error("ZephyrAPI not ready yet");
        }
        
        api.getClassById = function(id){
            return classIdDict[id];
        }

	api.getPersonalsClass = function(name) {
	    return findClass(ZephyrAPI.PERSONALS_TAG + name);
	}
        
        api.getInstanceById = function(id){
            return instanceIdDict[id];
        }
        
        api.getMessageById = function(id){
            return messageIdDict[id];
        }
        
        api.addSubscription = function(className, instanceName, recipientName, callback){
            checkReady();
            var sub = {
                class: className,
                instance: instanceName || "*",
                recipient: recipientName || "*"
            };
            return source.addSubscription(sub)
            .then(function(){
                api.subscriptions.push(sub);
                findClass(sub.class);
                return getOldMessages(sub, undefined, callback);
            }, api.onerror);
        }
        
        api.removeSubscription = function(className, instanceName, recipientName, callback){
            checkReady();
            var sub = {
                class: className,
                instance: instanceName || "*",
                recipient: recipientName || "*"
            };
            return source.removeSubscription(sub)
            .then(function(){
                var subs=[];
                for(var n=0; n<api.subscriptions.length; n++)
                    if(api.subscriptions[n].class != sub.class ||
                            api.subscriptions[n].instance != sub.instance ||
                            api.subscriptions[n].recipient != sub.recipient)
                        subs.push(api.subscriptions[n]);
		var cls = api.classDict[className];
		api.messages = api.messages.filter(function(m){
		    return m.parent_class != cls;
		});
		for(var n=0; n<cls.messages.length; n++)
		    delete messageIdDict[cls.messages[n].id];
		api.instances = api.instances.filter(function(i){
		    return i.parent_class != cls;
		});
		for(var n=0; n<cls.instances.length; n++)
		    delete instanceIdDict[cls.instances[n].id];
                api.classes = api.classes.filter(function(c){
		    return c != cls;
		});
                delete classIdDict[cls.id];
                delete api.classDict[className];
                api.subscriptions=subs;
                if (callback) {
                    return callback();
                }
            }, api.onerror);
        }
        
        api.getOldMessages = function(className, instanceName, recipientName, startdate, callback){
            checkReady();
            if(!instanceName)
                instanceName = "*";
            if(!recipientName)
                recipientName = "*";
            return getOldMessages({
                class: className,
                instance: instanceName,
                recipient: recipientName
            }, startdate, callback);
        }
        
        api.sendZephyr = function(params, callback){
            checkReady();
            return source.sendZephyr(params)
            .then(callback, api.onerror);
        }
        
        api.saveStorage = function(callback){
	    return source.saveStorage(api.storage)
	    .then(function(newStorage) {
                if (newStorage == api.storage) {
                    return true;
                }
                api.storage = newStorage;
                return false;
            }).then(callback, api.onerror);
	}

	api.getTickets = function(callback) {
	    if (typeof source.getTickets == "function")
		source.getTickets(callback);
	}

	api.denyTickets = function() {
	    if (typeof source.denyTickets == "function")
		source.denyTickets();
	}

	api.arePersonalsSupported = function() {
	    if (typeof source.arePersonalsSupported == "function")
		return source.arePersonalsSupported();
	    return false;
	}
        api.source = source;

    }

    ZephyrAPI.DISCONNECTED = "00 DISCONNECTED";
    ZephyrAPI.TICKETS_NEEDED = "01 TICKETS_NEEDED";
    ZephyrAPI.CONNECTING = "02 CONNECTING";
    ZephyrAPI.LOADING = "03 LOADING";
    ZephyrAPI.RECONNECTING = "04 RECONNECTING";
    ZephyrAPI.CONNECTED = "05 CONNECTED";
    ZephyrAPI.UPDATE_AVAILABLE = "UPDATE_AVAILABLE";
    ZephyrAPI.UPDATE_REQUIRED = "UPDATE_REQUIRED";
    
    ZephyrAPI.PERSONALS_TAG = "\u2194\u00A0";
    
    window.ZephyrAPI = ZephyrAPI;
})();

function hashStringToNumber(str){
    var sum=0;
    for(var n=0; n<str.length; n++){
        sum+=str.charCodeAt(n);
        sum*=17;
        sum%=32452843;
    }
    return sum;
}

function APISource() {
}

APISource.prototype.setStatus_ = function(newStatus) {
    if (newStatus != this.status) {
        this.status = newStatus;
        if (this.onstatuschange) {
            this.onstatuschange(newStatus);
        }
    }
}

APISource.prototype.dispatchMessages_ = function(messages) {
    if (this.onzephyr) {
        this.onzephyr(messages);
    }
}

APISource.prototype.maybeConvertClassToPersonal = function(message) {
    if (message.class &&
	message.class.replace(/\s/g, " ")
	.startsWith(ZephyrAPI.PERSONALS_TAG.replace(/\s/g, " "))) {
        message.recipient = message.class.substr(ZephyrAPI.PERSONALS_TAG.length);
        message.class = "message";	
    }
}

function NativeSource() {
    this.last_messaged = new Date() - 3*24*60*60*1000;
}

NativeSource.prototype = new APISource();

NativeSource.prototype.init = function() {
    this.setStatus_(ZephyrAPI.CONNECTING);
    return $.get("/user", null, null, "json")
    .then(function(data) {
        return {
            username: data.username,
            subscriptions: data.subscriptions,
            storage: JSON.parse(data.data)
        };
    });
}

NativeSource.prototype.procMessages = function (messages) {
    for(var n = 0; n < messages.length; n++) {
        if (messages[n].sender.match(/ \(UNAUTH\)$/)){
            messages[n].sender = messages[n].sender.replace(/ \(UNAUTH\)$/, "");
            messages[n].auth = false;
        }
        else {
            messages[n].auth = true;
        }
        
        if (messages[n].date > this.last_messaged) {
            this.last_messaged = messages[n].date;
        }
    }
    
    this.dispatchMessages_(messages);
}

NativeSource.prototype.start = function() {
    function getSubbedMessages(longpoll){
        var request = $.get("/chat", {
            startdate: this.last_messaged,
            longpoll: longpoll
        }, function(messages){
            this.setStatus_(ZephyrAPI.CONNECTED);
	    this.procMessages(messages);
            getSubbedMessages(true);
        }.bind(this), "json").error(function(){
            if(longpoll) {
                getSubbedMessages(false);
            }
            else {
                window.setTimeout(function(){getSubbedMessages(false)}, 10000);
                this.setStatus_(ZephyrAPI.RECONNECTING);
            }
        }.bind(this));
        window.setTimeout(function(){
            if(request.readyState!=4)
                request.abort();
        }, 60000);
    }
    getSubbedMessages = getSubbedMessages.bind(this);
    
    this.setStatus_(ZephyrAPI.LOADING);
    getSubbedMessages(false);
}

NativeSource.prototype.getOldMessages = function(sub, startdate) {
    return $.get("/chat", {
        class: sub.class,
        instance: sub.instance,
        recipient: sub.recipient,
        startdate: startdate-0,
        longpoll: false
    }, null, "json")
    .then(function(messages) {
	this.procMessages(messages);
	return messages;
    }.bind(this));
}

NativeSource.prototype.addSubscription = function(sub) {
    return $.post("/user", {
        action: "subscribe",
        class: sub.class,
        instance: sub.instance,
        recipient: sub.recipient
    });
}

NativeSource.prototype.removeSubscription = function(sub) {
    return $.post("/user", {
        action: "unsubscribe",
        class: sub.class,
        instance: sub.instance,
        recipient: sub.recipient
    });
}

NativeSource.prototype.sendZephyr = function(params) {
    this.maybeConvertClassToPersonal(params);
    return $.post("/chat", params);
}

NativeSource.prototype.saveStorage = function(data) {
    return $.post("/user", {
        action: "save_data",
        data: JSON.stringify(data)
    }).then(function() {
        return data;
    });
}

function RoostSource(filter) {
    this.filter = filter || {};
    this.last_messaged = 0;
    this.last_message_id = null;
    this.first_messaged = 1e100;
    this.first_message_id = null;
}

RoostSource.STORAGE_KEY = "zephyrplus_storage";

RoostSource.prototype = new APISource();

RoostSource.prototype.init = function() {
    var roost = this;
    this.storageManager = new StorageManager(new LocalStorageWrapper());
    this.ticketManager = new TicketManager(CONFIG.webathena, this.storageManager);
    this.roostApi = new API(CONFIG.server, CONFIG.serverPrincipal,
                            this.storageManager, this.ticketManager);
    this.model = new MessageModel(this.roostApi);

    roost.ticketManager.addEventListener("ticket-needed", function(ev) {
	roost.oldStatus = roost.status;
	roost.setStatus_(ZephyrAPI.TICKETS_NEEDED);
    });

    this.ticketManager.addEventListener("webathena-error", function() {
        console.log("Webathena error do something useful");
    });

    this.storageManager.addEventListener("usermismatch", function() {
	localStorage.clear();
	window.location.reload();
    });

    this.setStatus_(ZephyrAPI.CONNECTING);

    return Q.all([
	roost.storageManager.principal(),
        roost.roostApi.get('/v1/subscriptions'),
        roost.roostApi.get('/v1/info')
    ]).spread(function(username, subscriptions, info) {
        var at = username.lastIndexOf("@");
        if (at != -1) {
            roost.realm = username.substr(at + 1);
        }
        else {
            roost.realm = "";
        }
        
        roost.info = info;
        info.info = JSON.parse(info.info);
        info.info[RoostSource.STORAGE_KEY] = info.info[RoostSource.STORAGE_KEY] || {};
        
        return {
            username: username,
            storage: info.info[RoostSource.STORAGE_KEY],
            subscriptions: subscriptions
        }
    });
}

RoostSource.prototype.getTickets = function(cb) {
    this.ticketManager.refreshTickets({interactive: true});
    Q.all(
        [this.ticketManager.getTicket("server"),
         this.ticketManager.getTicket("zephyr")]
    ).then(function() {
	if (typeof cb == "function") {
	    cb();
	}
	this.setStatus_(this.oldStatus);
    }.bind(this));
}

RoostSource.prototype.stripRealm = function(sender) {
    if (sender.endsWith("@" + this.realm)) {
        return sender.substr(0, sender.lastIndexOf("@"));
    }
    return sender;
}

RoostSource.prototype.procMessages = function(messages) {
    for(var n=0; n<messages.length; n++) {
        if (messages[n].isPersonal) {
            messages[n].class = ZephyrAPI.PERSONALS_TAG + this.stripRealm(messages[n].conversation);
        }
        
        messages[n].sender = this.stripRealm(messages[n].sender);
        messages[n].date = messages[n].receiveTime;
        messages[n].auth = (messages[n].auth == 1);
        
        if (messages[n].date > this.last_messaged) {
            this.last_messaged = messages[n].date;
            this.last_message_id = messages[n].id;
        }
	
        if (messages[n].date < this.first_messaged) {
            this.first_messaged = messages[n].date;
            this.first_message_id = messages[n].id;
        }
	
	messages[n].id = messages[n].date + messages[n].id;
    }
    this.dispatchMessages_(messages);
}

RoostSource.prototype.start = function() {
    var oldMessages = [];
    var reverseTail = this.model.newReverseTail("", this.filter, function(messages, isDone) {
	oldMessages = messages.concat(oldMessages);
	if (!isDone && new Date() - messages[0].receiveTime < 3*24*60*60*1000 && oldMessages.length < 2000) {
	    reverseTail.expandTo(oldMessages.length + 200);
	}
	else {
	    this.procMessages(oldMessages);
	    reverseTail.close();
	    
	    this.setStatus_(ZephyrAPI.CONNECTED);

	    this.roostApi.addEventListener("disconnect", function() {
		this.setStatus_(ZephyrAPI.RECONNECTING);
	    }.bind(this));
	    this.roostApi.addEventListener("connect", function() {
		this.setStatus_(ZephyrAPI.CONNECTED);
	    }.bind(this));

	    // Roost doubles the reconnect delay after every failed
	    // reconnect, which is inconvenient
	    window.setInterval(function() {
		this.roostApi.reconnectTries_ = 1000;
		if (this.roostApi.reconnectDelay_ > 8000) {
		    this.roostApi.reconnectDelay_ = 8000;
		}
	    }.bind(this), 5000);

	    this.tail = this.model.newTail(this.last_message_id, this.filter, this.procMessages.bind(this));
	    this.tail.expandTo(100000);
	}
    }.bind(this));

    this.setStatus_(ZephyrAPI.LOADING);
    reverseTail.expandTo(200);
}

RoostSource.prototype.getOldMessages = function(sub, startdate) {
    return Q([]);
}

RoostSource.prototype.addSubscription = function(sub) {
    var sub = {
        class: sub.class,
        instance: sub.instance,
        recipient: sub.recipient == "*" ? "" : sub.recipient
    };
    return this.roostApi.post("/v1/subscribe", {
        subscriptions: [sub]
    }, {
        withZephyr: true,
        interactive: true
    });
}

RoostSource.prototype.removeSubscription = function(sub) {
    var sub = {
        class: sub.class,
        instance: sub.instance,
        recipient: sub.recipient == "*" ? "" : sub.recipient
    };
    return this.roostApi.post("/v1/unsubscribe", {
        subscription: sub
    }, {
        withZephyr: true,
        interactive: true
    });
}

RoostSource.prototype.sendZephyr = function(params) {
    this.maybeConvertClassToPersonal(params);

    var message = {class: params.class || "message",
		   instance: params.instance || "personal",
		   recipient: params.recipient || "",
		   opcode: "",
		   signature: params.signature || "",
		   message: params.message || ""
		  };
    
    if (!message.signature) {
	if (window.location.href.toLowerCase().match(/[a-z]+plus/)) {
            message.signature = "Sent from " +
		window.location.href.toLowerCase().match(/([a-z]+)plus/)[1][0].toUpperCase() +
		"+";
	}
	else {
	    message.signature = "";
	}
    }

    // The user can send a zephyr without clicking (with dot-enter),
    // so the tickets popup might get blocked.  Setting interactive to
    // false doesn't work, so we use this workaround.

    this.ticketManager.refreshTickets();

    return this.ticketManager.getTicket("zephyr").then(function() {
	return this.roostApi.post("/v1/zwrite", {
	    message: message
	}, {
	    withZephyr: true
	});
    }.bind(this));
}

RoostSource.prototype.saveStorage = function(data) {
    this.info.info[RoostSource.STORAGE_KEY] = data;
    return this.roostApi.post("/v1/info", {
        info: JSON.stringify(this.info.info),
        expectedVersion: this.info.version
    }).then(function(ret) {
        if (ret.updated) {
            this.info.version++;
            return data;
        }
        else {
            this.info.version = ret.version;
            this.info.info = JSON.parse(ret.info);
            if (!this.info.info[RoostSource.STORAGE_KEY]) {
                this.info.info[RoostSource.STORAGE_KEY] = data;
            }
            return this.info.info[RoostSource.STORAGE_KEY];
        }
    }.bind(this));
}

RoostSource.prototype.arePersonalsSupported = function() {
    return true;
}

function HybridSource() {
    this.nativeSource = new NativeSource();
    this.roostSource = new RoostSource({is_personal: true});

    this.roostEnabled = true;

    this.gotNativeMessages = false;
    this.gotRoostMessages = false;
    this.messageQueue = [];
    this.messagesDispatched = false;
}

HybridSource.prototype = new APISource();

HybridSource.prototype.init = function() {
    this.nativeSource.onzephyr = function(messages) {
	this.gotNativeMessages = true;
	this.procMessages(messages);
    }.bind(this);

    this.roostSource.onzephyr = function(messages) {
	this.gotRoostMessages = true;
	this.procMessages(messages);
    }.bind(this);

    this.nativeSource.onstatuschange = this.roostSource.onstatuschange =
	this.procStatusChange.bind(this);

    return this.nativeSource.init()
    .then(function(data) {
	this.roostSource.init()
	.then(function(roostData) {
	    if (roostData.username != data.username + "@" + this.roostSource.realm) {
		localStorage.clear();
		window.location.reload();
	    }
	    this.roostSource.start();
	}.bind(this));
	return data;
    }.bind(this));
}

HybridSource.prototype.getTickets = function (callback) {
    this.roostSource.getTickets(callback);
}

HybridSource.prototype.denyTickets = function () {
    this.roostEnabled = false;
    this.procStatusChange();
    this.procMessages([]);
}

HybridSource.prototype.procMessages = function(messages) {
    if (this.dispatchedMessages) {
	this.dispatchMessages_(messages);
	return;
    }

    this.messageQueue = this.messageQueue.concat(messages);
    if (this.gotNativeMessages && (!this.roostEnabled || this.gotRoostMessages)) {
	this.messageQueue.sort(function(a, b) {
	    return a.timestamp - b.timestamp;
	});
	this.dispatchMessages_(this.messageQueue);
	this.dispatchedMessages = true;
    }
}

HybridSource.prototype.procStatusChange = function() {
    var nativeStat = this.nativeSource.status;
    var roostStat = this.roostSource.status;

    if (!this.roostEnabled) {
	this.setStatus_(nativeStat);
    }
    else {
	this.setStatus_(nativeStat < roostStat ? nativeStat : roostStat);
    }
}

HybridSource.prototype.start = function() {
    this.nativeSource.start();
}

HybridSource.prototype.getOldMessages = function(sub, startdate) {
    if (this.roostEnabled && sub.recipient && sub.recipient != "*") {
	return this.roostSource.getOldMessages(sub, startdate);
    }
    return this.nativeSource.getOldMessages(sub, startdate);
}

HybridSource.prototype.addSubscription = function(sub) {
    if (this.roostEnabled && sub.recipient && sub.recipient != "*") {
	return this.roostSource.addSubscription(sub);
    }
    return this.nativeSource.addSubscription(sub);
}

HybridSource.prototype.removeSubscription = function(sub) {
    if (this.roostEnabled && sub.recipient && sub.recipient != "*") {
	return this.roostSource.removeSubscription(sub);
    }
    return this.nativeSource.removeSubscription(sub);
}

HybridSource.prototype.sendZephyr = function(params) {
    if (this.roostEnabled) {
	return this.roostSource.sendZephyr(params);
    }
    return this.nativeSource.sendZephyr(params);
}

HybridSource.prototype.saveStorage = function(data) {
    return this.nativeSource.saveStorage(data);
}

HybridSource.prototype.arePersonalsSupported = function() {
    return this.roostEnabled;
}


if (!String.prototype.startsWith) {
    String.prototype.startsWith = function startsWith(other) {
	return this.slice(0, other.length) == other;
    }
}

if (!String.prototype.endsWith) {
    String.prototype.endsWith = function endsWith(other) {
	return this.slice(this.length - other.length) == other;
    }
}
