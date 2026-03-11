system logging syslog server protocol
-------------------------------------

**Minimum user role:** operator

The default protocol for syslog services is UDP. You can change the protocol to the more reliable TCP protocol for important logs.

To configure the protocol for the syslog server:

**Command syntax: protocol [protocol]**

**Command mode:** config

**Hierarchies**

- system logging syslog


.. **Note**

	- no command set protocol to the default value

**Parameter table**

+-----------+---------------------------------------------------------+-------+---------+
| Parameter | Description                                             | Range | Default |
+===========+=========================================================+=======+=========+
| protocol  | The protocol based on which system messages are logged. | TCP   | UDP     |
|           |                                                         | UDP   |         |
+-----------+---------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog-server)# protocol tcp 
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-logging-syslog-server)# no protocol

.. **Help line:** Configure syslog server protocol

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+
| 11.0    | Applied new hierarchy |
+---------+-----------------------+


