system aaa-server radius timers hold-down
-----------------------------------------

**Minimum user role:** operator

Hold-down - prevents all requests from being sent to any AAA servers, as all AAA is performed locally based on locally configured users. It is triggered when all RADIUS servers are unavailable: requests are suppressed for a period of time in order to avoid delay on user login while waiting for a reply from unavailable servers.

To configure the RADIUS hold-down timer:

**Command syntax: hold-down [hold-down]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius


.. **Note**

	- Hold-down - prevent all radius requests from being sent to any radius servers.

	- The hold-down delay is triggered when all radius servers are found to be in an unavailable state.

	- The purpose of this delay is to limit unnecessary delays due to radius requests being sent to unavailable servers incurring the connection timeout.

	- If the delay is set to zero, the hold down delay is disabled and all radius servers are attempted

	- no command returns hold-down timers to their default values

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                                                   | Range    | Default |
+===========+===============================================================================================================+==========+=========+
| hold-down | The time (in seconds) that the NCR suppresses any AAA requests to any AAA servers.                            | 60..1200 | 600     |
|           | A value of zero disables the hold down delay and all servers are attempted or not, based on their reply-time. |          |         |
+-----------+---------------------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# timers
	dnRouter(cfg-aaa-radius-timers)# hold-down 300 
	

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa-radius)# no timers 
	dnRouter(cfg-aaa-radius-timers)# no hold-down

.. **Help line:** configure hold-down time for all the RADIUS servers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


