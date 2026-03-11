system logging syslog server port
---------------------------------

**Minimum user role:** operator

To set the port on which the syslog server listens to requests from clients.

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system logging syslog


.. **Note**

	- no command set port to the default value

**Parameter table**

+-----------+-----------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                           | Range    | Default |
+===========+=======================================================================+==========+=========+
| port      | The port on which the syslog server listens to requests from clients. | 1..65535 | 514     |
+-----------+-----------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog-server)# port 51021 
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-logging-syslog-server)# no port

.. **Help line:** Configure syslog server port

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 5.1.0   | Command introduced          |
+---------+-----------------------------+
| 6.0     | Applied new hierarchy       |
+---------+-----------------------------+
| 10.0    | Applied new hierarchy       |
+---------+-----------------------------+
| 11.0    | Applied new hierarchy       |
+---------+-----------------------------+
| 11.5.6  | Updated value of port range |
+---------+-----------------------------+


