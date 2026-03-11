debug bfd 
---------

**Command syntax: debug bfd** [parameter]

**Description:** Debug BFD events

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# debug bfd fsm
	dnRouter(cfg)# debug bfd packets
	dnRouter(cfg)# debug bfd hw
	dnRouter(cfg)# debug bfd
	
	dnRouter(cfg)# no debug bfd fsm
	dnRouter(cfg)# no debug bfd packets
	dnRouter(cfg)# no debug bfd hw
	dnRouter(cfg)# no debug bfd 
	
	dnRouter# set debug bfd fsm
	dnRouter# set debug bfd packets
	dnRouter# set debug bfd
	
	dnRouter# unset debug bfd fsm  
	dnRouter# unset debug bfd
	
	
**Command mode:** config

**TACACS role:**

TACACS role "operator" - debug logging is a persistant configuration

**Note:**

use "debug bfd" to enable all isis debug options

**Help line:**

**Parameter table:**

+-----------+------------------+------------------------------------------------+
| Parameter | Values           | description                                    |
+===========+==================+================================================+
| parameter | fsm              | bfd state machine events                       |
+-----------+------------------+------------------------------------------------+
|           | packets          | bfd send and received packets events           |
+-----------+------------------+------------------------------------------------+
|           | hw               | bfd hardware accelerator related information   |
+-----------+------------------+------------------------------------------------+

