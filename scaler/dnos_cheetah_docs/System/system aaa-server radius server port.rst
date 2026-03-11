system aaa-server radius server port 
-------------------------------------

**Minimum user role:** operator

To configure the UDP port for the remote RADIUS server:

**Command syntax: port [port]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


.. **Note**

	- no command reverts to default value

	- Up to 5 radius servers are supported

**Parameter table**

+-----------+-----------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                 | Range     | Default |
+===========+=============================================================================+===========+=========+
| port      | The destination port number to use when sending requests to the AAA server. | 1..65,535 | 1812    |
+-----------+-----------------------------------------------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
	dnRouter(cfg-aaa-radius-server)# port 100
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-aaa-radius-server)# no port

.. **Help line:** Configure RADIUS server port.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


