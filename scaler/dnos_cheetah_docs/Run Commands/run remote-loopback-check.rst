run remote-loopback-check
-------------------------

**Minimum user role:** operator

You can manually send probes to verify fiber and SFP functionality TX to RX.

Fiber loop verification is performed using ping. Echo packets are sent over looped interface (patch Tx to Rx) to validate the fiber and SFP by transmission and reciept of packets.

To run the fiber loop verification:

**Command syntax: un remote-loopback-check interface [interface-name]** count [count] interval [interval] size [size] timeout [timeout]

**Command mode:** operation

**Note**

- If a packet is sent with packet size bigger than path MTU, then MTU TX error counter will raise as no fragmentation is allowed.

- The minimum time interval (in seconds) between ping messages. The interval is max{interval, min{reply-time, timeout}}. That is, the highest value between the configured interval and either the echo reply receive time or the timeout (2 seconds) in case of no reply.

- Jitter is the standard-variation for delay between different echo requests.

- Round-trip-delay is computed over the successful echo requests only.

- User can stop ping requests using ctrl+c.

**Parameter table**

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+
| Parameter           | Description                                                                                                                                                                                                                                                                                                                                                 | Range                                                                         | Default                                               |
+=====================+=============================================================================================================================================================================================================================================================================================================================================================+===============================================================================+=======================================================+
| interface-name      | The interface from which to trigger the fiber verification test                                                                                                                                                                                                                                                                                             | 1..255 characters (an existing interface name)                                | \-                                                    |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+
| count               | The number of echo requests to send in a single probe.                                                                                                                                                                                                                                                                                                      | 1..1000000                                                                    | 1000                                                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+
| interval            | The minimum time interval (in seconds) between ping messages. The interval is max{interval, min{reply-time, timeout}. That is, the highest value between the configured interval and either the echo reply receive time or the timeout (2 seconds) in case of no reply.                                                                                     | 1..86400                                                                      | 1 millisecond                                         |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+
| size                | The size of echo request packets. If you set a size that is smaller than the minimum value, then the echo request packets will not be padded and the default size will be used instead. If packets are sent with an MTU packet size larger than the path MTU, the MTU TX error counter will increment as no fragmentation is allowed.                       | 1..65507                                                                      | 100 bytes                                             |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+
| timeout             | The time to wait before declaring an echo request as lost.                                                                                                                                                                                                                                                                                                  | 1..86400                                                                      | 2000 milliseconds                                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------+-------------------------------------------------------+


**Example**
::

	dnRouter# run remote-loopback-check interface ge100-0/0/15 timeout 10
	Sending 1000 Echo requests, size: 100, interface: ge100-0/0/15
	Timeout is 10 milliseconds, send interval is 1 millisecond:

	Legend:
	'!' - success, '.' - timeout

	Type ctrl+c to abort
	-2022-06-28 11:26:16.837322:

	!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!.!!!.!!!!.!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!.!!!!!.!!!.!!!!.!!!.!!!!.!!!!.!!!!!.!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!.!!!!!.!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!!.!!!.!!!!!.!!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!.!!!!.!!!!.!!!!!.!!!.!!!!.!!!!.!!!.!!!!.!!!!!.!!!!.!!!.!!!!.!!!!.!!!.!!!!!.!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!.!!!!!.!!!.!!!!.!!!.!!!!.!!!.!!!!!.!!!!.!!!.!!!!.!!!.!!!!.!!!!!.!

	Success rate is 88.10 percent (881/1000)
	Jitter: 0.01 msec
	Round-trip-delay (min/avg/max): 0.09/0.10/0.49 msec


	dnRouter# run remote-loopback-check interface ge100-0/0/1 count 10
	Sending 10 Echo requests, size: 100, interface: ge100-0/0/1
	Timeout is 2 milliseconds, send interval is 1 millisecond:

	Legend:
	'!' - success, '.' - timeout

	Type ctrl+c to abort
	-2022-06-22 12:58:37.347470:

	..........

	Success rate is 0.00 percent (0/10)
	Jitter: - msec
	Round-trip-delay (min/avg/max): -/-/- msec


	dnRouter# run remote-loopback-check interface ge100-0/0/1.250
	ERROR: Cannot set source interface 'ge100-0/0/0.250'. The source interface does not exist.


	dnRouter# run remote-loopback-check interface ge100-0/0/1
	ERROR: Cannot set source interface 'ge100-0/0/1'. Source interface must have admin-state enabled.


	dnRouter# run remote-loopback-check interface ge100-0/0/1
	ERROR: Cannot set source interface 'ge100-0/0/1'. Source interface must have an IPv4 address configured.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
