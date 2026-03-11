system aaa-server radius timers retry-time
------------------------------------------

**Minimum user role:** operator

Retry-time – prevents a failed server from being retried too soon. If a server is marked as "failed", it will not be used for requests until the retry time has expired. Once the retry time expires, the server may be marked as available to accept new requests.

To configure the retry-timer for all RADIUS servers:

**Command syntax: retry-time [retry-time]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius


.. **Note**

	- Retry-time -prevent a failed radius server from being retried too soon.

	- If a radius server is marked as failed, it will not be used for radius requests until the retry time has expired.

	- Once the retry time has expired, the radius server may be marked as available to accept new requests.

	- If the delay is set to zero, the retry delay is disabled and radius server is always attempted

	- no command returns retry-timer to the default value

**Parameter table**

+------------+------------------------------------------------------------------------------------------------------------------+----------+---------+
| Parameter  | Description                                                                                                      | Range    | Default |
+============+==================================================================================================================+==========+=========+
| retry-time | The time (in seconds) that the NCR waits after a server is marked as failed, without sending any requests to it. | 60..3600 | 1200    |
|            | A value of zero disables the retry-time delay and all servers are always attempted.                              |          |         |
+------------+------------------------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# timers
	dnRouter(cfg-aaa-radius-timers)# retry-time 600 
	

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa-radius)# no timers 
	dnRouter(cfg-aaa-radius-timers)# no retry-time 

.. **Help line:** configure retry-time for all the RADIUS servers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+

