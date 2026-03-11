show isis route
---------------

**Minimum user role:** viewer

To display IS-IS routing information:



**Command syntax: show isis** instance [isis-instance-name] **route** [prefix] level [level] table [table]

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances
	- nexthop-srgb-base represent the nexthop expected to handle the route level label. For ISIS-SR routes it means the nexthop which will get the SR prefix-sid label. In case of ti-lfa/uloop-avoidance usage, it may be a remote Q node

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------------+
| Parameter          | Description                                                                                                                    | Range                                           | Default value |
+====================+================================================================================================================================+=================================================+===============+
| isis-instance-name | Displays routes for a specific IS-IS instance. If you do not specify an instance, routes from all instances will be displayed. | 1..255 characters                               | \-            |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------------+
| prefix             | Filters the displayed routes to routes matching the specified prefix.                                                          | A.B.C.D/M xx:xx::xx:xx/X                        | \-            |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------------+
| level              | Filters the displayed routes to routes matching the specified level.                                                           | Level-1 Level-2                                 | Both levels   |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------------+
| table              | Filters the displayed routes to routes from the specified IS-IS table.                                                         | IPv4-unicast IPv6-unicast IPv4-shortcut IPv4-sr | All tables    |
|                    |                                                                                                                                | Ipv4-multicast Ipv6-sr                          |               |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------------+

**Example**
::

	dnRouter# show isis route

	Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
	  Instance METRO1
	IPv4 route table:
	  Level - 2
  	  Destination         Cost    Tag           Priority         NH-address                     Interface                                Interface-weight Egress-label
	  1.3.6.0/31          403     Untagged      N/A              1.3.18.0                       bundle-318.318                           1
	  1.3.17.0/31         330     Untagged      Medium           1.3.18.0                       bundle-318.318                           2
	  101.10.0.6/32       340     100           Medium           1.3.18.0                       bundle-318.318                           1
	  101.10.0.17/32      331     200           Low              1.3.18.0                       bundle-318.318                           1

	IPv6 route table:
	  Level - 2
  	  Destination         Cost    Tag           Priority         NH-address                     Interface                                Interface-weight Egress-label

	  Instance METRO1
	IPv4 shortcuts route table:
	  Level - 2
  	  Destination         Cost    Tag           Priority         NH-address                     Interface                                Interface-weight Egress-label
	  1.3.6.0/31          403     100           low              101.0.0.17                     auto_tunnel_sysp18_sysp17_P_CC_P_R1_4    N/A
	                                                             101.0.0.17                     auto_tunnel_sysp18_sysp17_P_CC_D_R1_3    N/A
	  100.0.0.3/32        300                                    100.0.0.3                      auto_tunnel_sysp18_sysp3_P_CC_D_R1_1     N/A
                                                                 100.0.0.3                      auto_tunnel_sysp18_sysp3_P_CC_P_R1_2     N/A
      Instance METRO1
    IPv4 segment-routing mpls table:
        Level - 2
        Destination   cost    nh-address        interface        egress-label   nexthop-srgb-base
        31.31.31.31   20      101.0.0.17        bundle-317       16031          16000


    dnRouter# show isis route 1.3.210.0/24

	 Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
	 Instance METRO1
	IPv4 route table:
	  Level - 2
	  Destination         Cost    Tag           Priority         NH-address                     Interface                                Interface-weight Egress-label
	  1.3.210.0/24        45      100           low              1.17.18.0                      bundle-1718                              1
                          60      100           low              12.0.0.2 (np)                  bundle-3                                 1

    dnRouter# show isis route table ipv4-sr

    Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
      Instance METRO1
    IPv4 segment-routing mpls table:
        Level - 2
        Destination      cost    nh-address        interface          egress-label
        31.31.31.31/32   20      101.0.0.17        bundle-317         16031
        20.20.20.20/32   100     101.0.0.17        bundle-317         51341(L)

    dnRouter# show isis route table ipv4-unicast

    Legend: lp - link-protecting LFA, np - node-protecting LFA, L - ldp-stitching, ul - microloop-avoidance
      Instance METRO1
    IPv4 route table:
      Level - 2
	  Destination         Cost    Tag           Priority         NH-address                     Interface                                Interface-weight Egress-label
      1.12.18.0/31        3       100           low              1.13.16.0 (ul)                 bundle-1316                              1                180000
      6.30.77.0/31        14      200           low              1.16.18.1 (ul)                 bundle-1618                              1                180023 6023


**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 9.0     | Command introduced                          |
+---------+---------------------------------------------+
| 13.0    | Added prefix filter to the syntax           |
+---------+---------------------------------------------+
| 14.0    | Added level and table filters to the syntax |
+---------+---------------------------------------------+
| 16.1    | Updated table filter values                 |
+---------+---------------------------------------------+
| 16.2    | Updated egress-label values                 |
+---------+---------------------------------------------+
| 16.3    | Added microloop legend                      |
+---------+---------------------------------------------+
| 18.1    | Added nh weight                             |
+---------+---------------------------------------------+
