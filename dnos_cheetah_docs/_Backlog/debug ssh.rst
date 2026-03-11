debug ssh 
----------

**Command syntax: debug ssh** [parameter]

**Description:** Debug ssh events

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# debug ssh
	dnRouter(cfg)# debug ssh server
	dnRouter(cfg)# debug ssh server remote-connection-state
	dnRouter(cfg)# debug ssh server acl-blocked-connections
	dnRouter(cfg)# debug ssh server max-login-entry
	dnRouter(cfg)# debug ssh client 
	dnRouter(cfg)# debug ssh client local-connection-state
	dnRouter(cfg)# debug ssh client failed-connection
	
	
	
	dnRouter(cfg)# no debug ssh
	dnRouter(cfg)# no debug ssh server
	dnRouter(cfg)# no debug ssh server remote-connection-state
	dnRouter(cfg)# no debug ssh server acl-blocked-connections
	dnRouter(cfg)# no debug ssh server max-login-entry
	dnRouter(cfg)# no debug ssh client 
	dnRouter(cfg)# no debug ssh client local-connection-state
	dnRouter(cfg)# no debug ssh client failed-connection
	
	
	dnRouter# set debug ssh server acl-blocked-connections
	dnRouter# set debug ssh server max-login-entry
	dnRouter# set debug ssh client 
	
	dnRouter# no set debug ssh server max-login-entry
	dnRouter# no set debug ssh client 
	
	
**Command mode:** operational/config

**TACACS role:**

TACACS role "operator" - debug logging is a persistent configuration

**Note:**

-  debug ssh - to enabled all ssh debug options

-  no debug ssh - to disable all ssh debug options

-  debug ssh client - to enabled all ssh client debug options

-  no debug ssh client - to disable all ssh client debug options

-  debug ssh server - to enabled all ssh debug server options

-  no debug ssh server - to disable all ssh debug server options

**Help line:**

**Parameter table:**

+-----------+---------------------------------------------------------------------------+---------------------------+
| Parameter | Values                                                                    | description               |
+===========+===========================================================================+===========================+
| parameter | **server**                                                                | ssh server debug command  |
|           |                                                                           |                           |
|           | {remote-conncection-state \| acl-blocked-connections \| max-login-entry } |                           |
+-----------+---------------------------------------------------------------------------+---------------------------+
|           | **clients**                                                               | ssh client debug commands |
|           |                                                                           |                           |
|           | { local-connection-state \| failed-connections}                           |                           |
+-----------+---------------------------------------------------------------------------+---------------------------+
