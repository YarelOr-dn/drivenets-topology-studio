show ldp neighbors
------------------

**Minimum user role:** viewer

To display information on LDP neighbors:



**Command syntax: show ldp neighbors** [neighbor-address] detail

**Command mode:** operational



**Note**

- Although local Graceful Restart Recovery and Reconnect timeouts are configured in seconds the Remote Reconnect and Recovery timeouts are presented in milliseconds to match how these values are delivered in the FT Session TLV session parameters.

- LDP message statistics refer to LDP TCP session messages. There might be several LDP messages packed within a TCP packet. For example, 'Initialization' message and 'KeepAlive' messages are commonly packed together. Alos 'Address' and 'Label Mapping' messages are packed in the same TCP packet.

..	- Specifying [neighbor-address] displays the specific neighbor information only.

..	- Specifying 'detail' displays detailed information per neighbor including LDP message statistics.

..	- Graceful Restart detail view: Although local GR Recovery and Reconnect timeouts are configured in seconds the Remote Reconnect and Recovery timeouts are presented in milliseconds to match how these values are delivered in the FT Session TLV session parameters.

..	- LDP message statistics refer to LDP TCP session messages. Note, there might be several LDP messages packed within a TCP packet. For example, 'Initialization' message and 'KeepAlive' messages are commonly packed together as well as 'Address' and 'Label Mapping' messages are packed in the same TCP packet.

..	- the TLVs combination per LDP message type is constant unless vendor specific TLV are added, in which case peer LDP routers from different vendor may show different TLV set.

..	- LDP messages counter verification should be done with care to message packing and occurring events and peering state machine.
	Counters verification may use well known peer from other well-known vendor.

- Capabilities section shows locally and remotely supported capabilities as advertised between peers. If a capability is supported on both ends on the session initialization then it will be apply for the session. If a local capability was not advertised by DNOS when the session was established and at a later stage it was enabled by user, then as Dynamic Capability Announcement is not supported the state change of the capability will not take affect until after the session is reset, which shall require the operator's intervention.

..  - Capabilities are advertised and counted for LDP message statistics as an Initialization message when advertised within. Capability messages are used used to track state changes of capabilities advertised in the Initialization message, and will not be counted as Dynamic Capability Announcement is currently not supported.


**Parameter table**

+------------------+-------------------------------------------------------------------------------+---------+---------+
| Parameter        | Description                                                                   | Range   | Default |
+==================+===============================================================================+=========+=========+
| neighbor-address | Filters the displaed information to the specified LDP neighbor.               | A.B.C.D | \-      |
+------------------+-------------------------------------------------------------------------------+---------+---------+
| detail           | displays detailed information per neighbor, including LDP message statistics. | \-      | \-      |
+------------------+-------------------------------------------------------------------------------+---------+---------+


**Example**
::

	dnRouter# show ldp neighbors


	Legend: t - Targeted neighbor r - nsr recovered

	-----------------------------------------------------------------------------------------------------------------
	| Peer LDP Identifier  | Session IP            | State         | Uptime               | Session Remaining time  |
	-----------------------------------------------------------------------------------------------------------------
	| 2.2.2.2           (t)|  2.2.2.2              | OPERATIONAL   | 0 days 11:36:18      | 164 sec                 |
	| 3.3.3.3           (t)|  3.3.3.3              | OPERATIONAL   | 0 days 11:36:19      | 160 sec                 |
	| 7.7.7.7           (t)|  7.7.7.7              | OPERATIONAL   | 0 days 11:36:56      | 25 sec                  |
	| 11.11.11.11          |  11.11.11.11          | OPERATIONAL   | 0 days 11:36:56      | 25 sec                  |
	| 209.0.0.1            |  27.100.1.2           | OPERATIONAL   | 0 days 11:36:33      | 146 sec                 |
	| 209.0.0.2            |  27.100.2.2           | OPERATIONAL   | 0 days 11:36:27      | 152 sec                 |
	| 209.0.0.3            |  27.100.3.2           | OPERATIONAL   | 0 days 11:36:33      | 146 sec                 |
	| 209.0.0.4            |  27.100.4.2           | OPERATIONAL   | 0 days 11:36:33      | 146 sec                 |


	dnRouter# show ldp neighbors detail

	Peer LDP Identifier: 2.2.2.2:0
	  TCP connection: 1.1.1.1:646 - 2.2.2.2:34719
	  Session Holdtime: Negotiated: 180 sec, [Local: 180 sec, Remote: 180 sec], Remaining 152 sec
	  State: OPERATIONAL
	  Label Adv. mode: Downstream-Unsolicited
	  Uptime: 11:40:31
	  Rcv-addr-withdraw-delay: 0 sec Remaining: 0 sec
	  Capabilities:
	  	Multipoint:
			Local - P2MP: enabled, MBB: disabled
			Remote - P2MP: disabled, MBB: disabled
		Graceful restart:
			Local - Restart: enabled, Helper mode: enabled
			Remote - Restart: enabled, Helper mode: enabled
			Remote reconnect timeout: 60000 ms
			Remote recovery time: 120000 ms
	  LDP Discovery Sources:
	    IPv4:
	      Interface: ge100-0/0/12
	        Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 12 sec
	          Local Hello Interval: 5 sec
	      Targeted Hello: 2.2.2.2     reason: discovery-accept ldp-tunneling rLFA
	        Hello Holdtime: Negotiated: 90 sec, [Local: 90 sec, Remote: 90 sec], Remaining 82 sec
	          Local Hello Interval: 10 sec
	      Interface: ge100-1/0/4
	        Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 14 sec
	          Local Hello Interval: 5 sec

	  Message Statistics:                Sent              Rcvd
	  ------------------            ---------         ---------
	      Initialization                    1                 1
		  Capability                        0                 0
	      Address                           1                 1
	      Address-Withdraw                  0                 0
	      Label-Mapping                  4333              4075
	      Label-Withdraw                    0                 0
	      Label-Release                     0                36
	      Label-Request                     0                 0
	      Label-Abort-Request               0                 0
	      Notification                      0                 0
	      KeepAlive                       701               701
	      Targeted Hello                 4207              4208
	      Total                          9243              9022

	Peer LDP Identifier: 3.3.3.3:0
	  TCP connection: 1.1.1.1:646 - 3.3.3.3:55329
	  Session Holdtime: Negotiated: 180 sec, [Local: 180 sec, Remote: 180 sec], Remaining 148 sec
	  State: OPERATIONAL
	  Label Adv. mode: Downstream-Unsolicited
	  Uptime: 11:40:32
	  Rcv-addr-withdraw-delay: 0 sec Remaining: 0 sec
	  Capabilities:
	  	Multipoint:
			Local - P2MP: enabled, MBB: disabled
			Remote - P2MP: enabled, MBB: enabled
		Graceful restart:
			Local - Restart: enabled, Helper mode: enabled
			Remote - Restart: disabled, Helper mode: disabled
			Remote reconnect timeout: 0 ms
			Remote recovery time: 0 ms
	  LDP Discovery Sources:
	    IPv4:
	      Targeted Hello: 3.3.3.3     reason: discovery-accept ldp-tunneling
	        Hello Holdtime: Negotiated: 90 sec, [Local: 90 sec, Remote: 90 sec], Remaining 89 sec
	          Local Hello Interval: 10 sec

	  Message Statistics:                Sent              Rcvd
	  ------------------            ---------         ---------
	      Initialization                    1                 1
		  Capability                        0                 0
	      Address                           1                 1
	      Address-Withdraw                  0                 0
	      Label-Mapping                  4333              4073
	      Label-Withdraw                    0                 0
	      Label-Release                     0                 0
	      Label-Request                     0                 0
	      Label-Abort-Request               0                 0
	      Notification                      0                 0
	      KeepAlive                       701               701
	      Targeted Hello                 4207              4208
	      Total                          9243              8984

	Peer LDP Identifier: 7.7.7.7:0
	  TCP connection: 1.1.1.1:646 - 7.7.7.7:51692
	  Session Holdtime: Negotiated: 30 sec, [Local: 180 sec, Remote: 30 sec], Remaining 23 sec
	  State: OPERATIONAL
	  Label Adv. mode: Downstream-Unsolicited
	  Uptime: 11:41:09
	  Rcv-addr-withdraw-delay: 0 sec Remaining: 0 sec
	  Capabilities:
	  	Multipoint:
			Local - P2MP: enabled, MBB: enabled
			Remote - P2MP: enabled, MBB: enabled
		Graceful restart:
			Local - Restart: enabled, Helper mode: enabled
			Remote - Restart: enabled, Helper mode: enabled
			Remote reconnect timeout: 120000 ms
			Remote recovery time: 0 ms
	  LDP Discovery Sources:
	    IPv4:
	      Interface: ge100-0/0/1.25
	        Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 13 sec
	          Local Hello Interval: 5 sec
	      Targeted Hello: 7.7.7.7     reason: discovery-accept ldp-tunneling
	        Hello Holdtime: Negotiated: 45 sec, [Local: 90 sec, Remote: 45 sec], Remaining 37 sec
	          Local Hello Interval: 10 sec

	  Message Statistics:                Sent              Rcvd
	  ------------------            ---------         ---------
	      Initialization                    1                 1
		  Capability                        0                 0
	      Address                           1                 1
	      Address-Withdraw                  0                 0
	      Label-Mapping                  4333              3571
	      Label-Withdraw                    0                 8
	      Label-Release                     8                 0
	      Label-Request                     0                 0
	      Label-Abort-Request               0                 0
	      Notification                      0                 0
	      KeepAlive                      4204              4206
	      Targeted Hello                 4207              3206
	      Total                         12754             10993


	dnRouter# show ldp neighbors 11.11.11.11 detail

	Peer LDP Identifier: 11.11.11.11:0
	  TCP connection: 1.1.1.1:646 - 11.11.11.11:56742
	  Session Holdtime: Negotiated: 30 sec, [Local: 180 sec, Remote: 30 sec], Remaining 22 sec
	  State: OPERATIONAL
	  Label Adv. mode: Downstream-Unsolicited
	  Uptime: 11:40:30
	  Rcv-addr-withdraw-delay: 0 sec Remaining: 0 sec
	  Capabilities:
	  	Multipoint:
			Local - P2MP: enabled, MBB: enabled
			Remote - P2MP: enabled, MBB: enabled
		Graceful restart:
			Local - Restart: enabled, Helper mode: enabled
			Remote - Restart: enabled, Helper mode: enabled
			Remote reconnect timeout: 120000 ms
			Remote recovery time: 0 ms
	  LDP Discovery Sources:
	    IPv4:
	      Interface: ge100-0/0/4.210
	        Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 14 sec
	          Local Hello Interval: 5 sec
	      Interface: bundle-100.20
	        Hello Holdtime: Negotiated: 15 sec, [Local: 15 sec, Remote: 15 sec], Remaining 12 sec
	          Local Hello Interval: 5 sec

	  Message Statistics:                Sent              Rcvd
	  ------------------            ---------         ---------
	      Initialization                    1                 1
		  Capability                        0                 0
	      Address                           1                 1
	      Address-Withdraw                  0                 0
	      Label-Mapping                  4333              3575
	      Label-Withdraw                    0                12
	      Label-Release                    12                 0
	      Label-Request                     0                 0
	      Label-Abort-Request               0                 0
	      Notification                      0                 0
	      KeepAlive                      4200              4202
	      Targeted Hello                    0                 0
	      Total                          8547              7791

.. **Help line:** Displays LDP neighbors information.

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 6.0     | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 10.0    | Added the detail option                                                           |
+---------+-----------------------------------------------------------------------------------+
| 11.0    | Removed the detail option                                                         |
+---------+-----------------------------------------------------------------------------------+
| 13.0    | Added the detail and neighbor-address options, added support for graceful restart |
+---------+-----------------------------------------------------------------------------------+
| 17.1    | Extended the capabilities section to include mLDP information                     |
+---------+-----------------------------------------------------------------------------------+
