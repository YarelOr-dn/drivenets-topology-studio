system aaa-server radius server retry-interval
----------------------------------------------

**Minimum user role:** operator

When the NCR sends a request to the RADIUS server, it will wait a configured length of time for a response from the RADIUS server before resending the request if no response is received.

To configure the interval to wait for a response from the RADIUS server:

**Command syntax: retry-interval [interval]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


**Note**

- Notice the change in prompt.

.. - no command reverts retry-interval to default value

**Parameter table**

+----------------+------------------------------------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                                          | Range   | Default |
+================+======================================================================================================+=========+=========+
| retry-interval | The length of time the NCR waits for a response from the RADIUS server before resending the request. | 1..1000 | 5       |
+----------------+------------------------------------------------------------------------------------------------------+---------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
	dnRouter(cfg-aaa-radius-server)# retry-interval 30
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-aaa-radius-server)# no retry-interval


.. **Help line:** Configure RADIUS server request retries interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

