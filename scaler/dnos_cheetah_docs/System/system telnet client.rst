system telnet client
--------------------

**Minimum user role:** operator

To configure the Telnet client parameters.

**Command syntax: client**

**Command mode:** config

**Hierarchies**

- system telnet

**Note**

- Notice the change in prompt.

.. - no command returns the configuration to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# client
	dnRouter(cfg-system-telnet-client)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-telnet)# no client

.. **Help line:** configures Telnet client.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


