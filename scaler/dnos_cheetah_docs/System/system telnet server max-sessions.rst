system telnet server max-sessions
---------------------------------

**Minimum user role:** operator

The system supports up to 32 concurrent Telnet sessions. To change the number of concurrent sessions allowed on the system:

**Command syntax: server max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- system telnet server

.. **Note**

	-  no command returns the number of maximum sessions to default

**Parameter table**

+--------------+--------------------------------------------------+-------+---------+
| Parameter    | Description                                      | Range | Default |
+==============+==================================================+=======+=========+
| max-sessions | The maximum number of concurrent telnet sessions | 1..32 | 10      |
+--------------+--------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# server
	dnRouter(cfg-system-telnet-server)# max-sessions 5
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-telnet-server)# no max-sessions

.. **Help line:** configure maximum number of concurrent telnet sessions to Telnet server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


