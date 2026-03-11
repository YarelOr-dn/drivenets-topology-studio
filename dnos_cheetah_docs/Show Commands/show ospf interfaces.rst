show ospf interfaces
--------------------

**Minimum user role:** viewer

The show ospf interfaces command displays concentric information on the OSPF process on all OSPF-enabled interfaces, if an interface name is not specified. If specified, then the OSPF configuration for the requested interface is displayed.


**Command syntax: show ospf** instance [ospf-instance-name] **interfaces** [interface-name | detail]

**Command mode:** operational



**Note**

- SRLG values are only defined on interfaces and only when MPLS traffic-engineering is enabled on the related area.

.. 	- SRLG values are only defined on interfaces, on which SRLG values are defined and only when mpls traffic-engineering is enabled on the related area.

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances


**Parameter table**

+--------------------+----------------------------------------------------------------+-------------------------------------------------------+---------------+
| Parameter          | Description                                                    | Values                                                | Default value |
+====================+================================================================+=======================================================+===============+
| interface-name     | Filters the displayed information for a specified interface    | ge<interface speed>-<A>/<B>/<C>                       | all           |
|                    |                                                                | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>    |               |
|                    |                                                                | bundle-<bundle id>                                    |               |
|                    |                                                                | bundle-<bundle id>.<sub-interface id>                 |               |
|                    |                                                                | lo<lo-interface id>                                   |               |
+--------------------+----------------------------------------------------------------+-------------------------------------------------------+---------------+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance. | configured instances names                            | all           |
+--------------------+----------------------------------------------------------------+-------------------------------------------------------+---------------+
| detail             | Prints detailed information on interfaces                      |                                                       |               |
+--------------------+----------------------------------------------------------------+-------------------------------------------------------+---------------+

**Example**
::

	dnRouter# show ospf instance instance1 interfaces 

	OSPF instance instance1
	Interface                                         State     Type                Area      
	bundle-2.1011                                     Up        POINT-TO-POINT      0.0.0.0   
	bundle-2.1012                                     Up        POINT-TO-POINT      0.0.0.2   
	lo0                                               Up        LOOPBACK            0.0.0.0   

	dev-dnRouter(cfg)# show ospf interfaces 

	OSPF instance instance1
	Interface                                         State     Type                Area      
	bundle-2.1011                                     Up        POINT-TO-POINT      0.0.0.0   
	bundle-2.1012                                     Up        POINT-TO-POINT      0.0.0.2   
	lo0                                               Up        LOOPBACK            0.0.0.0   

	OSPF instance instance2
	Interface                                         State     Type                Area      
	ge100-0/0/1                                       Up        POINT-TO-POINT      0.0.0.0   
	lo1                                               Up        LOOPBACK            0.0.0.0   

	dnRouter# show ospf interfaces detail

	Ospf Instance instance1
	bundle-2.1011 is up
	  ifindex 17, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.0.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Fast-reroute backup-candidate: enabled
	  Router ID 100.70.1.45, Network Type POINT-TO-POINT, Cost: 10
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Point-To-Point, Priority 1
	  No designated router on this network
	  No backup designated router on this network
	  Multicast group memberships: OSPFAllRouters
	  Timer intervals configured: Hello 15s, Dead 60s, Wait 60s, Retransmit 5
	    Hello due in 14.284s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  Message digest authentication enabled
	    Youngest key id is 1
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: disabled
	  SRLG Values:
	    232

	bundle-2.1012 is up
	  ifindex 15, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.1.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Router ID 100.70.1.45, Network Type BROADCAST, Cost: 10
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Backup, Priority 1
	  Designated Router (ID) 10.170.1.66, Interface Address 10.170.1.66
	  Backup Designated Router (ID) 100.70.1.45, Interface Address 10.170.1.65
	  Saved Network-LSA sequence number 0x80000141
	  Multicast group memberships: OSPFAllRouters OSPFDesignatedRouters
	  Timer intervals configured: Hello 10s, Dead 40s, Wait 40s, Retransmit 5
	    Hello due in 2.742s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  Simple authentication enabled
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: disabled
	  SRLG Values:
	    232
	    96


	dnRouter# show ospf instance instance1 interfaces detail

	Ospf Instance instance1

	lo0 is up
	  ifindex 6 <UP,BROADCAST,LOOPBACK,RUNNING,NOARP>
	  Internet Address 10.170.1.1/32, Area 0.0.0.0
	  Router ID 10.170.1.45, Network Type LOOPBACK, Cost: 1
	  No designated router on this network
	  No backup designated router on this network
	  Multicast group memberships: <None>

	bundle-2.1011 is up
	  ifindex 17, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.0.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Fast-reroute backup-candidate: enabled
	  Adjacency-SID advertisement: enabled
	  Router ID 100.70.1.45, Network Type POINT-TO-POINT, Cost: 10
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Point-To-Point, Priority 1
	  No designated router on this network
	  No backup designated router on this network
	  Multicast group memberships: OSPFAllRouters
	  Timer intervals configured: Hello 15s, Dead 60s, Wait 60s, Retransmit 5
	    Hello due in 14.284s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  Message digest authentication enabled
	    Youngest key id is 1
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: disabled
	  SRLG Values:
	    232

	bundle-2.1012 is up
	  ifindex 15, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.1.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Router ID 100.70.1.45, Network Type BROADCAST, Cost: 10
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Backup, Priority 1
	  Designated Router (ID) 10.170.1.66, Interface Address 10.170.1.66
	  Backup Designated Router (ID) 100.70.1.45, Interface Address 10.170.1.65
	  Saved Network-LSA sequence number 0x80000141
	  Multicast group memberships: OSPFAllRouters OSPFDesignatedRouters
	  Timer intervals configured: Hello 10s, Dead 40s, Wait 40s, Retransmit 5
	    Hello due in 2.742s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  Simple authentication enabled
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: disabled
	  SRLG Values:
	    232
	    96


	dnRouter# show ospf interfaces ge100-1/2/2

	Ospf Instance instance1
	bundle-2.1011 is up
	  ifindex 17, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.0.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Router ID 100.70.1.45, Network Type POINT-TO-POINT, Cost: 10 (cost-mirroring)
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Point-To-Point, Priority 1
	  No designated router on this network
	  No backup designated router on this network
	  Multicast group memberships: OSPFAllRouters
	  Timer intervals configured: Hello 15s, Dead 60s, Wait 60s, Retransmit 5
	    Hello due in 11.629s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: enabled


	dnRouter# show ospf instance instance1 interfaces ge100-1/2/2

	Ospf Instance instance1
	bundle-2.1011 is up
	  ifindex 17, MTU 9192 bytes, BW 0 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
	  Internet Address 10.170.0.65/30, Area 0.0.0.0
	  MTU mismatch detection:enabled
	  Router ID 100.70.1.45, Network Type POINT-TO-POINT, Cost: 10 (cost-mirroring)
	  LDP Sync is disabled
	  Transmit Delay is 1 sec, State Point-To-Point, Priority 1
	  No designated router on this network
	  No backup designated router on this network
	  Multicast group memberships: OSPFAllRouters
	  Timer intervals configured: Hello 15s, Dead 60s, Wait 60s, Retransmit 5
	    Hello due in 11.629s
	  Neighbor Count is 1, Adjacent neighbor count is 1
	  BFD: Admin state: Enabled
	       Minimum Tx Interval: 250
	       Minimum Rx-Interval: 250
	       BFD Multiplier: 3
	       RSVP dependency: enabled


.. **Help line:** Displays concentric information on the OSPF process on all OSPF-enabled interfaces

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 18.2    | Added instance parameter |
+---------+--------------------------+
| v19.0   | Added detail parameter   |
+---------+--------------------------+
