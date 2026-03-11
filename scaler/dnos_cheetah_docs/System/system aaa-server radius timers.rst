system aaa-server radius timers
-------------------------------

**Minimum user role:** operator

RADIUS servers have two timers that can be configured individually:

Retry-time – prevents a failed server from being retried too soon. If a server is marked as "failed", it will not be used for requests until the retry time has expired. Once the retry time expires, the server may be marked as available to accept new requests.

Hold-down - prevents all requests from being sent to any servers. It is triggered when all servers are unavailable: requests are suppressed for a period of time in order to avoid a connection timeout.

To configure the RADIUS timers, enter the timers configuration mode:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- system aaa-server radius


**Note**

- Notice the change in prompt.

.. - Retry-time -prevent a failed RADIUS server from being retried too soon.

	- If a RADIUS server is marked as failed, it will not be used until the retry time has expired.

	- Once the retry time has expired, the RADIUS server may be marked as available to accept new requests.

	- If the delay is set to zero, the retry delay is disabled and RADIUS server is always attempted

	- Hold-down - prevent all RADIUS requests from being sent to any RADIUS servers.

	- The hold-down delay is triggered when all RADIUS servers are found to be in an unavailable state.

	- The purpose of this delay is to limit unnecessary delays due to RADIUS requests being sent to unavailable servers incurring the connection timeout.

	- If the delay is set to zero, the hold down delay is disabled and all RADIUS servers are attempted

	- Retry-time and hold-down can be set individually, together and in any order.

	-  no command returns timers to their default values


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius 
	dnRouter(cfg-system-aaa-radius)# timers
	dnRouter(cfg-aaa-radius-timers)# retry-time 600 
	dnRouter(cfg-aaa-radius-timers)# hold-down 300 
	

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-aaa-tacacs)# no timers 
	dnRouter(cfg-aaa-tacacs-timers)# no retry-time 
	dnRouter(cfg-aaa-tacacs-timers)# no hold-down

.. **Help line:** Configure RADIUS servers retry-time and hold-down timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


