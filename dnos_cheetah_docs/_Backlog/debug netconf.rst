debug netconf 
--------------

**Command syntax: debug netconf** [parameter]

**Description:** Debug NETCONF events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug netconf
	dnRouter(cfg)# debug netconf messages
	dnRouter(cfg)# debug netconf events
	
	dnRouter(cfg)# no debug netconf messages
	dnRouter(cfg)# no debug netconf events
	
	
	dnRouter# set debug netconf messages
	dnRouter# set debug netconf events
	
	dnRouter# no set debug netconf messages
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  setting "debug netconf" will enable all debug features

| debug netconf messages
| displays part of the netconf messages running between clients and server:
| - RPCs received from the NetConf clients specifying NetConf session-ID, NetConf user and IP-address
| - RPCs responses sent towards the NetConf clients (specifying NetConf session-ID, NetConf user and IP-address) from the NetConf server
| - displays netconf keepalive messages between client and server

debug netconf events

-  displays all the user netconf configurations changes

-  session up/down state changes with specifying source-IP of the netconf client

-  blocked connections due to attached client-list

-  blocked connections due to max-sessions exceeded

-  blocked connections due to authentication failures

**Help line:** Debug NETCONF events

**Parameter table:**

+-----------+----------+------------------------+
| Parameter | Values   | description            |
+===========+==========+========================+
| parameter | messages | Debug NETCONF messages |
+-----------+----------+------------------------+
|           | events   | Debug NETCONF events   |
+-----------+----------+------------------------+
