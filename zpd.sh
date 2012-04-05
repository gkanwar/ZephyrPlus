#! /bin/bash
kinit daemon/zephyrplus.xvm.mit.edu -k -t /ZephyrPlus/zephyrplus-new-keytab
zwgc -subfile /ZephyrPlus/.zephyrs.subs -f /ZephyrPlus/.zwgc.desc -ttymode -nofork
