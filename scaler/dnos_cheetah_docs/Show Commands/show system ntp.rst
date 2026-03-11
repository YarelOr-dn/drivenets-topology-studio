show system ntp 
----------------

**Minimum user role:** viewer

Network Timing Protocol (NTP) is used to synchronize time and clocks across network connections. Use the following command to display the network time protocol (NTP) status. This command shows the status of NTP neighbors in order to determine if NTP is working and communicating properly.

**Command syntax: show system ntp**

**Command mode:** operational

**Note**

- Only remote NTP servers configured with admin-state enabled will be presented.

..
	**Internal Note**

	- Command implementing "ntpq -pn" linux command

	- Remote: neighbors configured as NTP servers

	- | * = current time source
	- | # = source selected, distance exceeds maximum value
	- | o = source selected, Pulse Per Second used
	- | + = source selected, included in final set
	- | x = source false ticker
	- | . = source selected from end of candidate list
	- | - = source discarded by cluster algorithm

	- Refid: remote source's synchronization source

	- Stratum: stratum level of the source

	- Types: types available

	- l = local

	- u = unicast

	- m = multicast

	- b = broadcast

	- = netaddr

	- When: sec since last received packet

	- Poll: polling interval, in seconds, for source

	- Reach: indicates success/failure to reach source, 377 all attempts successful

	- Delay: indicates the roundtrip time to receive a reply [ms]

	- Offset: indicates the time difference between the client server and source [ms]

	- Jitter: indicates the difference between two samples [ms]

	- VRF: the name of the VRF default (in-band management)VRF mgmt0 (out-of-band management)

**Parameter table**

The following information is displayed:

+-----------+------------------------------------------------------------------------------------------+
| Parameter | Description                                                                              |
+===========+==========================================================================================+
| Remote    | The neighbors configured as NTP servers. See Remote legend above                         |
+-----------+------------------------------------------------------------------------------------------+
| Refid     | The remote source's synchronization source                                               |
+-----------+------------------------------------------------------------------------------------------+
| Stratum   | The stratum level of the source                                                          |
+-----------+------------------------------------------------------------------------------------------+
| Types     | See Types legend above                                                                   |
+-----------+------------------------------------------------------------------------------------------+
| When      | The number of seconds since the last packet was received                                 |
+-----------+------------------------------------------------------------------------------------------+
| Poll      | The polling interval, in seconds, for the source                                         |
+-----------+------------------------------------------------------------------------------------------+
| Reach     | Indicates success/failure to reach source. 377 means that all attempts are successful.   |
+-----------+------------------------------------------------------------------------------------------+
| Delay     | Indicates the roundtrip time to receive a reply (in milliseconds)                        |
+-----------+------------------------------------------------------------------------------------------+
| Offset    | Indicates the time difference between the client server and the source (in milliseconds) |
+-----------+------------------------------------------------------------------------------------------+
| Jitter    | Indicates the difference between two samples (in milliseconds)                           |
+-----------+------------------------------------------------------------------------------------------+

The following information is displayed on each NTP neighbor:

+---------+------------------------------------------------------------------------------------------+
| Field   | Description                                                                              |
+=========+==========================================================================================+
| Remote  | The neighbors specified in the ntp.conf file. The following indicators may be displayed: |
|         |                                                                                          |
|         | \* = current time source                                                                 |
|         |                                                                                          |
|         | # = source selected, distance exceeds maximum value                                      |
|         |                                                                                          |
|         | o = source selected, Pulse Per Second used                                               |
|         |                                                                                          |
|         | \+ = source selected, included in final set                                              |
|         |                                                                                          |
|         | x = source false ticker                                                                  |
|         |                                                                                          |
|         | . = source selected from end of candidate list                                           |
|         |                                                                                          |
|         | – = source discarded by cluster algorithm                                                |
+---------+------------------------------------------------------------------------------------------+
| Refid   | The remote source’s synchronization source                                               |
+---------+------------------------------------------------------------------------------------------+
| Stratum | The stratum level of the source                                                          |
+---------+------------------------------------------------------------------------------------------+
| Types   | The following types are available:                                                       |
|         |                                                                                          |
|         | l = local                                                                                |
|         |                                                                                          |
|         | u = unicast                                                                              |
|         |                                                                                          |
|         | m = multicast                                                                            |
|         |                                                                                          |
|         | b = broadcast                                                                            |
|         |                                                                                          |
|         | \– = netaddr                                                                             |
+---------+------------------------------------------------------------------------------------------+
| When    | The time since the last NTP packet was received from the peer.                           |
+---------+------------------------------------------------------------------------------------------+
| Poll    | The polling interval (in seconds) between NTP poll packets.                              |
+---------+------------------------------------------------------------------------------------------+
| Reach   | Indicates success or failure to reach the source. 377 = all attempts were successful.    |
+---------+------------------------------------------------------------------------------------------+
| Delay   | Indicates the round trip time (in milliseconds) to receive a reply                       |
+---------+------------------------------------------------------------------------------------------+
| Offset  | The calculated offset (in milliseconds) between the client server and source's time.     |
+---------+------------------------------------------------------------------------------------------+
| Jitter  | Indicates the difference (in milliseconds) between two samples.                          |
+---------+------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system ntp
	Legend: 
	
	Remote: 
	* = current time source
	# = source selected, distance exceeds maximum value
	o = source selected, Pulse Per Second used
	+ = source selected, included in final set
	x = source false ticker
	. = source selected from end of candidate list
	 = source discarded by cluster algorithm
	
	Types: 
	l = local 
	u = unicast 
	m = multicast
	b = broadcast
	 = netaddr
	
	| VRF      | Remote           | Refid         | Stratum | Types | When | Poll | Reach | Delay  | Offset  | Jitter |
	+----------+------------------+---------------+---------+-------+------+------+-------+--------+---------+--------|
	| default  | +109.226.40.40   | 216.229.0.179 | 2       | u     | 548  | 1024 | 177   | 6.578  |  1.338  | 2.021  |
	| default  | *91.189.89.189   | 17.253.34.253 | 2       | u     | 500  | 1024 | 377   | 67.753 | -2.258  | 2.147  |
	

.. **Help line:** show ntp status

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 5.1.0   | Command introduced                               |
+---------+--------------------------------------------------+
| 6.0     | Updated command from show ntp to show system ntp |
+---------+--------------------------------------------------+

