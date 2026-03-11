system aaa-server radius server retries
---------------------------------------

**Minimum user role:** operator

When the NCR sends a request to the RADIUS server, the expectation is for the server to respond. If no response is received, the NCR will wait for the configured retry-interval before attempting again. It will attempt to send the request the configured maximum number of retries, after which it will mark the RADIUS server as "unavailable" and send the request to the next available RADIUS server (according to the configured priority).

To configure the maximum number of retries:

**Command syntax: retries [num-of-retries]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


.. **Note**

	- no command reverts retries to default value

**Parameter table**

+-----------+-------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                       | Range | Default |
+===========+===================================================================+=======+=========+
| retries   | The maximum number of times to send requests to the RADIUS server | 1..50 | 3       |
+-----------+-------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
	dnRouter(cfg-aaa-radius-server)# retries 4
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-aaa-radius-server)# no retries


.. **Help line:** Configure RADIUS server request retries number

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


