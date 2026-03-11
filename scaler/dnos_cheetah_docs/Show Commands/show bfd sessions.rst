show bfd sessions
-----------------

**Minimum user role:** viewer

To display information on BFD sessions:

**Command syntax: show bfd sessions** detail vrf [vrf-name] {tunnel [tunnel-name] \| {discriminator [discriminator] address-family [address-family] local-address [ip-address] neighbor [neighbor-address] interface [interface-name] client [client] }}

**Command mode:** operational


..
	**Internal Note**

	- session in Init state will no display Uptime/Downtime

	- can have multiple clients per session

	- for micro-BFD session, interface is the physical interface and client is the bundle interface name

	- for Multi-hop BFD session, nothing will be displayed under interface

	- Session Tx/Rx/Multiplier are session negotiated parmeters. For session in Init or Down state, nothing will be displayed

	- when setting neighbor address or detail, displays detailed information


**Parameter table**

+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| Parameter        | Description                                                                                                            | Range                                 | Default |
+==================+========================================================================================================================+=======================================+=========+
| discriminator    | Display only the BFD session matching the specified local discriminator                                                | 0..4294967295                         | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| tunnel-name      | Display only the BFD sessions protecting the specified RSVP tunnel                                                     | String 1..255 characters              | \-      |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| address-family   | Display only BFD sessions where neighbor address matches the address-family. BFD for RSVP will be ipv4 address-family. | IPv4                                  | \-      |
|                  |                                                                                                                        | IPv6                                  |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| ip-address       | Display only the BFD sessions matching the specified local address.                                                    | A.B.C.D                               | \-      |
|                  | When neighbor-address is specified, the local-address must match the address-family of the neighbor-address.           | xx:xx::xx:xx                          |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| neighbor-address | Display only the BFD sessions matching the specified neighbor address.                                                 | A.B.C.D                               | \-      |
|                  | When local-address is specified, the neighbor-address must match the address-family of the local -address.             | xx:xx::xx:xx                          |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| interface-name   | Display only single-hop BFD sessions with egress interface matching the specified interface-name                       | bundle-<bundle-id>                    | \-      |
|                  |                                                                                                                        | bundle-<bundle-id>.<sub-interface-id> |         |
|                  |                                                                                                                        | ge<interface speed>-<A>/<B>/<C>       |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| client           | Display only the BFD sessions matching the specified client                                                            | Bundle interface name                 | \-      |
|                  |                                                                                                                        | BGP                                   |         |
|                  |                                                                                                                        | Static                                |         |
|                  |                                                                                                                        | RSVP                                  |         |
|                  |                                                                                                                        | IS-IS                                 |         |
|                  |                                                                                                                        | OSPF                                  |         |
|                  |                                                                                                                        | OSPFv3                                |         |
|                  |                                                                                                                        | segment-routing                       |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+
| vrf-name         | Any configured VRF name. The following VRFs exist by default:  default, mgmt0, mgmt-ncc-0, mgmt-ncc-1                  | \-                                    | Default |
|                  | Use 'all' to view routes in all VRFs. When not specified the default VRF sessions are displayed.                       |                                       |         |
|                  |                                                                                                                        |                                       |         |
|                  |                                                                                                                        |                                       |         |
+------------------+------------------------------------------------------------------------------------------------------------------------+---------------------------------------+---------+

**Example**
::

	dnRouter# show bfd sessions

	Legend: R - RSVP dependency

	vrf: default
	IPv4:
	| neighbor address   | state   | session          | Uptime/Downtime   | clients         | interface/Policy+Path   |
	|                    |         | Tx/Rx/Multiplier |                   |                 |                         |
	|--------------------+---------+------------------+-------------------+-----------------+-------------------------|
	| 1.2.3.4            | up      |                  | 2 days, 00:00:2   | ospf (R)        |                         |
	| 9.9.9.9            | up      |                  | 2 days, 00:00:2   | ospfv3          |                         |
	| 2.2.2.2            | Down    |                  | 0 days, 00:00:2   | bgp, ospf       |                         |
	| 10.170.6.66        | Init    |                  |                   | bundle-3        | ge100-1/0/2             |
	| 10.170.6.66        | Init    |                  |                   | bundle-3        | ge100-1/0/3             |
	| 2.2.2.2            | Up      | 300/300/3        | 0 days, 18:42:45  | rsvp            | TUNNEL_1                |
	| 10.170.7.1         | Up      | 300/300/3        | 0 days, 00:40:1   | static, bgp     | bundle-1                |
	| 5.5.5.4            | Up      | 400/400/3        | 0 days, 1:04:55   | segment-routing | Tun3_Color2             |
	|                    |         |                  |                   |                 | (SA2_Adj-L1)            |
	| 5.5.5.6            | Up      | 400/400/3        | 0 days, 1:04:55   | segment-routing | Tun7_Color666666        |
	|                    |         |                  |                   |                 | (NCS-Label)             |

	IPv6:
	| neighbor address   | state   | session          | Uptime/Downtime   | clients     | interface   |
	|                    |         | Tx/Rx/Multiplier |                   |             |             |
	|--------------------+---------+------------------+-------------------+-------------+-------------|
	| 2001::66           | Up      | 400/400/3        | 0 days, 18:24:45  | bgp         |             |

	dnRouter# show bfd sessions discriminator 100
	dnRouter# show bfd sessions neighbor 1.2.3.4
	dnRouter# show bfd sessions vrf CLIENT_1 neighbor 1.2.3.4
	dnRouter# show bfd sessions local-address 1.2.3.3 neighbor 1.2.3.4
	dnRouter# show bfd sessions local-address 2001:ab12::2
	dnRouter# show bfd sessions interface ge10-2/1/1
	dnRouter# show bfd sessions local-address 4.4.4.4 client rsvp
	dnRouter# show bfd sessions client rsvp neighbor 5.5.5.5

	dnRouter# show bfd sessions discriminator 8 interface ge100-0/0/1

	Legend: R - RSVP dependency

	IPv4:

	| neighbor address   | state   | session Tx/Rx/Multiplier   | Uptime/Downtime   | clients     | interface   |
	|--------------------+---------+----------------------------+-------------------+-------------+-------------|
	| 1.11.12.0          | Down    |                            | 0 days, 2:55:33   | bundle-1112 | ge100-0/0/1 |


	dnRouter# show bfd sessions vrf all

	vrf:default
	IPv4:
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| neighbor address | state | session          | Uptime/Downtime | clients   | interface |
	|                  |       | Tx/Rx/Multiplier |                 |           |           |
	+==================+=======+==================+=================+===========+===========+
	| 1.2.3.4          | Up    | /-               | 2 days, 00:00:2 | ospf (R)  | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| 9.9.9.9          | Up    | /-               | 2 days, 00:00:2 | ospfv3    | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| 2.2.2.2          | Down  | /-               | 0 days, 00:00:2 | bgp, ospf | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+

	IPv6:
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| neighbor address | state | session          | Uptime/Downtime | clients   | interface |
	|                  |       | Tx/Rx/Multiplier |                 |           |           |
	+==================+=======+==================+=================+===========+===========+
	| 2001::66         | Up    | 400/400/3        | 0 days, 18:24:45| bgp       | /-        |
	...

	vrf:vrf_a
	IPv4:
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| neighbor address | state | session          | Uptime/Downtime | clients   | interface |
	|                  |       | Tx/Rx/Multiplier |                 |           |           |
	+==================+=======+==================+=================+===========+===========+
	| 1.2.3.4          | Up    | /-               | 2 days, 00:00:2 | ospf (R)  | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| 9.9.9.9          | Up    | /-               | 2 days, 00:00:2 | ospfv3    | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| 2.2.2.2          | Down  | /-               | 0 days, 00:00:2 | bgp, ospf | /-        |
	+------------------+-------+------------------+-----------------+-----------+-----------+

	IPv6:
	+------------------+-------+------------------+-----------------+-----------+-----------+
	| neighbor address | state | session          | Uptime/Downtime | clients   | interface |
	|                  |       | Tx/Rx/Multiplier |                 |           |           |
	+==================+=======+==================+=================+===========+===========+
	| 2001::66         | Up    | 400/400/3        | 0 days, 18:24:45| bgp       | /-        |
	...


	dnRouter# show bfd sessions address-family ipv6

	vrf: default
	IPv6:
	| neighbor address   | state   | session          | Uptime/Downtime   | clients     | interface   |
	|                    |         | Tx/Rx/Multiplier |                   |             |             |
	|--------------------+---------+------------------+-------------------+-------------+-------------|
	| 2001::66           | Up      | 400/400/3        | 0 days, 18:24:45  | bgp         |             |


	dnRouter# show bfd sessions detail

	vrf: default
	| neighbor address   | state   | session          | Uptime/Downtime   | clients     | interface   |
	|                    |         | Tx/Rx/Multiplier |                   |             |             |
	|--------------------+---------+------------------+-------------------+-------------+-------------+
	| 10.170.7.1         | Up      | 300/300/3        | 0 days, 00:40:1   | static, bgp | bundle-1    |
	Local Diag: No Diagnostic(0), Demand mode: 0, Poll bit: 0
	Remote-state: Up
	BFD type: single-hop BFD
	Echo mode: Disabled
	Version: 1
	Address-family: IPv4 TTL: 255
	Local address: 10.170.6.65
	Local port: 49161, Remote port: 3784
	Detection time: 900ms
	Local Discriminator: 20000, Remote Discriminator: 335
	Local MinTx: 300msec, Local MinRx: 300msec, Local Multiplier: 3
	Received MinTx: 300msec, Received MinRx: 300msec, Received Multiplier: 3
	Local detection timeout: 900msec  Remote detection timeout: 900msec
	Up transitions: 1 Failure transitions: 0 Detection time timeouts: 0
	Rx packets Count: 3980             Tx packets Count: 3955
	Last received packet sample:
	     Version: 1               Diagnostic: No Diagnostic(0)
	     State bit: Down   Demand bit: 0  Poll bit: 1   C-bit: 1  Final bit: 0
	     Multiplier: 3            Length: 24
	     My Discr: 335 	     Your Discr: 20000
	     Min tx interval: 300000  Min rx interval: 300000


	| neighbor address   | state   | session          | Uptime/Downtime   | clients     | interface   |
	|                    |         | Tx/Rx/Multiplier |                   |             |             |
	|--------------------+---------+------------------+-------------------+-------------+-------------|
	| 2.2.2.2            | Up      | 300/300/3        | 0 days, 18:42:45  | rsvp        | TUNNEL_1    |
	Local Diag: No Diagnostic(0), Demand mode: 0, Poll bit: 0
	Remote-state: Up
	BFD type: BFD over MPLS
	Echo mode: Disabled
	Version: 1
	Address-family: IPv4 TTL: 255
	Local address: 1.1.1.1
	Local port: 49162, Remote port: 3784
	Detection time: 900ms
	Local Discriminator: 15456, Remote Discriminator: 32938
	Local MinTx: 300msec, Local MinRx: 300msec, Local Multiplier: 3
	Received MinTx: 3300msec, Received MinRx: 300msec Received Multiplier: 3
	Local detection timeout: 900msec  Remote detection timeout: 900msec
	Up transitions: 1 Failure transitions: 0 Detection time timeouts: 0
	Rx packets Count: 3980             Tx packets Count: 3955
	Last received packet sample:
	     Version: 1               Diagnostic: No Diagnostic(0)
	     State bit: Down   Demand bit: 0  Poll bit: 1   C-bit: 1  Final bit: 0
	     Multiplier: 3            Length: 24
	     My Discr: 15456	      Your Discr: 32938



	| neighbor address   | state   | session          | Uptime/Downtime   | clients     | interface   |
	|                    |         | Tx/Rx/Multiplier |                   |             |             |
	|--------------------+---------+------------------+-------------------+-------------+-------------|
	| 10.170.6.66        | Init    |                  |                   | bundle-3    | ge100-1/0/2 |
	Local Diag: No Diagnostic(0), Demand mode: 0, Poll bit: 0
	Remote-state:
	BFD type: Micro BFD
	Echo mode: Disabled
	Version: 1
	Address-family: IPv4 TTL: 255
	Local address: 10.170.6.65
	Local port: 49163, Remote port: 6784
	Detection time:
	Local Discriminator: 100, Remote Discriminator: 0
	Local MinTx: 300msec, Local MinRx: 300msec, Local Multiplier: 3
	Received MinTx:  ,    Received MinRx:       Received Multiplier:
	Local detection timeout:   Remote detection timeout:
	Up transitions:   Failure transitions: 0 Detection time timeouts: 0
	Rx packets Count: 0             Tx packets Count: 2
	Last received packet sample:
	     Version:                Diagnostic:
	     State bit:     Demand bit:    Poll bit:     C-bit:    Final bit:
	     Multiplier:              Length:
	     My Discr:     	      Your Discr:

	| neighbor address   | state   | session Tx/Rx/Multiplier   | Uptime/Downtime   | clients         | interface/Policy+Path   |
	|--------------------+---------+----------------------------+-------------------+-----------------+-------------------------|
	| 5.5.5.4            | Up      | 400/400/3                  | 0 days, 1:04:56   | segment-routing | Tun3_Color2             |
	|                    |         |                            |                   |                 | (SA2_Adj-L1)            |
	Local Diag: none, Demand mode: 0, Poll bit:
	Remote-state: Up
	BFD type: Seamless BFD
	BFD session location: NCP 1
	Echo mode: Disabled
	Version: 1
	Address-family: IPv4 TTL: 255
	Local address: 5.5.5.1
	Local port: 4784, Remote port: 7784
	Detection time: 1200ms
	Local Discriminator: 4148, Remote Discriminator: 5554
	Local MinTx: 400msec, Local MinRx: 0msec, Local Multiplier: 3
	Received MinTx: 400ms, Received MinRx: 5ms, Received Multiplier: 3
	Up transitions: 0 Failure transitions: 0 Detection time timeouts: 0
	Rx packets Count: 583        Tx packets Count: 583
	Last received packet sample:
		Version:           1          Diagnostic:      none
		State bit: Up Demand bit:  Poll bit:  C-bit:  Final bit:
		Multiplier:        3          Length:          24
		My Discr:          5554       Your Discr:      4148
		Min tx interval:   400        Min rx interval: 5
		Min Echo interval: 0          RSVP dependency: 0

	dnRouter# show bfd sessions detail discriminator 100
	dnRouter# show bfd sessions detail neighbor 1.2.3.4
	dnRouter# show bfd sessions detail local-address 1.2.3.3 neighbor 1.2.3.4
	dnRouter# show bfd sessions detail local-address 2001:ab12::2
	dnRouter# show bfd sessions detail interface ge10-2/1/1
	dnRouter# show bfd sessions detail local-address 4.4.4.4 client rsvp
	dnRouter# show bfd sessions detail client rsvp neighbor 5.5.5.5

.. **Help line:**

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 11.2    | Command introduced                                 |
+---------+----------------------------------------------------+
| 11.4    | Introduced new optional address-family parameter   |
+---------+----------------------------------------------------+
| 11.6    | Added support for BFD for OSPF and OSPFv3 (client) |
+---------+----------------------------------------------------+
| 12.0    | Added support for BFD for IS-IS (client)           |
+---------+----------------------------------------------------+
| 16.1    | Added support for VRF                              |
+---------+----------------------------------------------------+
| 18.3    | Added support for Seamless-BFD sessions            |
+---------+----------------------------------------------------+
