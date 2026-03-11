show ospfv3 interfaces
----------------------

**Minimum user role:** viewer

The show ospfv3 interfaces command displays concentric information on the OSPFv3 process on all OSPFv3-enabled interfaces, if an interface name is not specified. If specified, then the OSPFv3 configuration for the requested interface is displayed.


**Command syntax: show ospfv3 interfaces** [interface-name | detail]

**Command mode:** operational



**Note**

- SRLG values are only defined on interfaces and only when MPLS traffic-engineering is enabled on the related area.

.. - interface-name is optional

**Parameter table**

+----------------+-------------------------------------------------------------+----------------------------------------------------+---------------+
| Parameter      | Description                                                 | Values                                             | Default value |
+================+=============================================================+====================================================+===============+
| interface-name | Filters the displayed information for a specified interface | ge<interface speed>-<A>/<B>/<C>                    | all           |
|                |                                                             | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |               |
|                |                                                             | bundle-<bundle id>                                 |               |
|                |                                                             | bundle-<bundle id>.<sub-interface id>              |               |
|                |                                                             | lo<lo-interface id>                                |               |
+----------------+-------------------------------------------------------------+----------------------------------------------------+---------------+
| detail         | Prints detailed information on interfaces                   |                                                    |               |
+----------------+-------------------------------------------------------------+----------------------------------------------------+---------------+

**Example**
::

  dnRouter#  show ospfv3 interfaces

	Interface                                         State     Type                Area
	ge100-0/0/3.1001                                  Up        POINT-TO-POINT      0.0.0.0
	ge100-0/0/4.10                                    Up        POINT-TO-POINT      0.0.0.0
	lo0                                               Up        LOOPBACK            0.0.0.0

  dnRouter#  show ospfv3 interfaces detail

  ge100-0/0/3.1001 is up
    ifindex 14472, MTU 1500 bytes, BW 100000000 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
      Link Local address fe80::1abe:92ff:fea0:5203, Interface ID 0, Area 0.0.0.0
    MTU mismatch detection:enabled
    Router ID 22.22.22.22, Network type POINT-TO-POINT, Cost: 1
    Transmit Delay 1 sec, State PointToPoint, Priority 1
    No designated router on this network
    No backup designated router on this network
    Multicast group memberships: OSPFv3AllRouters
    Timer intervals configured: Hello 10s, Dead 40s, Retransmit 5s
      Hello due in 1.417s
    Neighbor Count is 1, Adjacent neighbor count is 1

  ge100-0/0/4.10 is up
    ifindex 14472, MTU 1500 bytes, BW 100000000 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
      Link Local address fe80::1abe:92ff:fea0:5203, Interface ID 0, Area 0.0.0.0
    MTU mismatch detection:enabled
    Router ID 22.22.22.22, Network type POINT-TO-POINT, Cost: 1
    Transmit Delay 1 sec, State PointToPoint, Priority 1
    No designated router on this network
    No backup designated router on this network
    Multicast group memberships: OSPFv3AllRouters
    Timer intervals configured: Hello 10s, Dead 40s, Retransmit 5s
      Hello due in 1.417s
    Neighbor Count is 1, Adjacent neighbor count is 1
    IPsec AH authentication enabled, SPI 256, MD5 algorithm
    BFD: Admin state: Enabled
       Minimum Tx Interval: 300
       Minimum Rx Interval: 300
       BFD Multiplier: 3

  lo0 is up
    ifindex 9217 <UP,BROADCAST,LOOPBACK,RUNNING,NOARP>
      Link Local address fe80::202:3ff:fe04:506, Interface ID 0, Area 0.0.0.0
    Router ID 100.70.1.124, Network type LOOPBACK, Cost: 0
    No designated router on this network
    No backup designated router on this network
    Multicast group memberships: OSPFv3AllRouters

.. **Help line:** Displays concentric information on the OSPFv3 on all OSPFv3-enabled interfaces

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 11.6    | Command introduced                        |
+---------+-------------------------------------------+
| 17.0    | Added IPsec AH authentication information |
+---------+-------------------------------------------+
| 19.1    | Added detail parameter                    |
+---------+-------------------------------------------+
