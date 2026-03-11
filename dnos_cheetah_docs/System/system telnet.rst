system telnet
--------------

**Minimum user role:** operator

The Telnet server enables interaction with a Telnet client through the telnet protocol. It allows to manage the system over telnet via in-band and via out-of-band management networks.

To enter Telnet configuration mode:

**Command syntax: telnet [parameters]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt.

.. - no command returns the state to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet
	dnRouter(cfg-system-telnet)# client admin-state enabled
	dnRouter(cfg-system-telnet)# server
	dnRouter(cfg-system-telnet-server)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-telnet)# no client admin-state

.. **Help line:** configure telnet server and client functionality.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


