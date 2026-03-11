show route summary
------------------

**Minimum user role:** viewer

The show route summary command displays the number of IPv4 routes and IPv6 routes stored in the routing table per protocol. You can filter the display by protocol and VRF.

**Command syntax: show route summary** {vrf [vrf-name] | all} \| [protocol-name] \| table [table]

**Command mode:** operational

**Note**

- Note that IPv4 and IPv6 route tables are displayed on separate columns.

- By default, the command output includes ipv4-unicast, ipv6-unicast, and mpls-nh routing summary

- When a vrf name is not specified, the default vrf will be shown as default

- When 'all' is specified, a summary is displayed for each vrf

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------------+
| Parameter     | Description                                                                                        | Value                                                      | Default value |
+===============+====================================================================================================+============================================================+===============+
| protocol-name | The name of the protocol to filter by.                                                             | access - the number of default routes obtained via DHCP/RA | \-            |
|               |                                                                                                    | connected - the number of locally configured interfaces    |               |
|               |                                                                                                    | static - the number of configured static routes            |               |
|               |                                                                                                    | ospf - the number of OSPF routes                           |               |
|               |                                                                                                    | isis - the number of IS-IS routes                          |               |
|               |                                                                                                    | ebgp - the number of eBGP routes                           |               |
|               |                                                                                                    | ibgp - the number of iBGP routes                           |               |
|               |                                                                                                    | rsvp - the number of RSVP routes                           |               |
+---------------+----------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------------+
| vrf-name      | Filter the display results based on the name of the VRF. Enter all to display routes for all VRFs. | string  | all                                              | default       |
+---------------+----------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------------+
| table         | Displays the requested table with the number of routes (or flowspec rules) installed.              | ipv4-unicast                                               | all           |
|               |                                                                                                    | ipv6-unicast                                               |               |
|               |                                                                                                    | mpls-nh                                                    |               |
|               |                                                                                                    | color-mpls-nh                                              |               |
|               |                                                                                                    | color-mpls-ipv6-nh                                         |               |
|               |                                                                                                    | ipv4-flowspec                                              |               |
|               |                                                                                                    | ipv6-flowspec                                              |               |
+---------------+----------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------------+


**Example**
::

	dnRouter# show route summary

	VRF: default
	Table: ipv4-unicast, ipv6-unicast

	| Protocol   | IPv4 Routes   | IPv6 Routes   |
	+------------+---------------+---------------+
	| access     | 0             | 0             |
	| connected  | 498           | 492           |
	| static     | 303           | 1             |
	| isis       | 5877          | 3576          |
	| ospf       | 0             | 0             |
	| ebgp       | 105578        | 3949          |
	| ibgp       | 35207         | 5002          |
	| rsvp       | 0             | 0             |
	| Totals     | 147521        | 13020         |

	RIB maximum IPv4 routes: 2025000
	RIB maximum IPv6 routes: 525000
	RIB maximum IGP IPv4 routes: 25000
	RIB maximum IGP IPv6 routes: 25000
	BGP maximum IPv4 routes: 2000000
	BGP maximum IPv6 routes: 500000

	Table: mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| isis       | 5877          |
	| isis-sr    | 0             |
	| ospf       | 0             |
	| ospf-sr    | 0             |
	| ldp        | 244           |
	| rsvp       | 4             |
	| Totals     | 6125          |

	Table: color-mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| isis-sr    | 40            |
	| ospf-sr    | 20            |
	| sr-te      | 20            |
	| Totals     | 80            |

	Table: color-mpls-nh-ipv6

	| Protocol   | IPv6 Routes   |
	|------------+---------------|
	| isis-sr    | 40            |
	| ospf-sr    | 20            |
	| sr-te      | 20            |
	| Totals     | 80            |

	Table: ipv4-flowspec, ipv6-flowspec

	| Protocol   | IPv4 flows    | IPv6 flows    |
	|------------+---------------+---------------|
	| Totals     | 0             | 0             |

	Table: multicast-ipv4-rpf, RPF check mode: intact

	| Protocol   | IPv4 Unicast Routes   | IPv4 Multicast Routes |
	|------------+-----------------------+-----------------------|
	| connected  | 498                   |                       |
	| static     | 303                   |                       |
	| isis       | 5877                  |  52                   |
	| ebgp       | 105578                |                       |
	| ibgp       | 35207                 |  101                  |
	| Totals     | 147463                |  153                  |


	dnRouter# show route summary table ipv4-unicast

	VRF: default
	Table: ipv4-unicast

	| Protocol   | IPv4 Routes   |
	+------------+---------------+
	| access     | 0             |
	| connected  | 498           |
	| static     | 303           |
	| isis       | 5877          |
	| ospf       | 0             |
	| ebgp       | 105771        |
	| ibgp       | 35207         |
	| rsvp       | 0             |
	| Totals     | 147714        |


	dnRouter# show route summary table color-mpls-nh

	VRF: default
	Table: color-mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
        | sr_te      | 100           |
        | Totals     | 100           |


	dnRouter# show route summary table color-mpls-nh-ipv6

	VRF: default
	Table: color-mpls-nh-ipv6

	| Protocol   | IPv6 Routes   |
	|------------+---------------|
        | sr_te      | 100           |
        | Totals     | 100           |


	dnRouter# show route summary protocol isis

	VRF: default
	Table: ipv4-unicast, ipv6-unicast

	| Protocol   | IPv4 Routes   | IPv6 Routes   |
	|------------+---------------+---------------|
	| isis       | 5877          | 3576          |

	Table: mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| isis       | 5877          |

	Table: multicast-ipv4-rpf, RPF check mode: MRPF

	| Protocol   | IPv4 Unicast Routes   | IPv4 Multicast Routes |
	|------------+-----------------------+-----------------------|
	| isis       |                       |  52                   |


	dnRouter# show route summary vrf MyVrf1

	VRF: MyVrf1
	Table: ipv4-unicast, ipv6-unicast

	| Protocol   | IPv4 Routes   | IPv6 Routes   |
	+------------+---------------+---------------+
	| access     | 0             | 1             |           
	| connected  | 498           | 492           |
	| static     | 303           | 1             |
	| isis       | 5877          | 3576          |
	| ospf       | 0             | 0             |
	| ebgp       | 105578        | 3949          |
	| ibgp       | 35207         | 5002          |
	| rsvp       | 0             | 0             |
	| Totals     | 147521        | 13020         |

	Table: mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| isis       | 5877          |
	| ospf       | 0             |
	| Totals     | 5934          |

	Table: ipv4-flowspec, ipv6-flowspec

	| Protocol   | IPv4 flows    | IPv6 flows    |
	|------------+---------------+---------------|
	| Totals     | 0             | 0             |

	Table: multicast-ipv4-rpf

	| Protocol   | IPv4 Routes   |
	|------------+---------------+
	| connected  | 498           |
	| static     | 303           |
	| isis       | 5877          |
	| ebgp       | 105578        |
	| ibgp       | 35207         |
	| Totals     | 147463        |


	dnRouter# show route summary vrf test

	VRF: test
	Table: ipv4-unicast, ipv6-unicast

	| Protocol   | IPv4 Routes   | IPv6 Routes   |
	+------------+---------------+---------------+
	| connected  | 318           | 16            |
	| ebgp       | 70882         | 6909          |
	| ibgp       | 32656         | 2751          |
	| static     | 1002          | 1005          |
	| Totals     | 110795        | 14007         |

	RIB maximum IPv4 routes(maximum/threshold): 2025000/75%
	RIB maximum IPv6 routes(maximum/threshold): 525000/75%


	dnRouter# show route summary vrf new_limit

	VRF: new_limit
	Table: ipv4-unicast, ipv6-unicast

	| Protocol   | IPv4 Routes   | IPv6 Routes   |
	|------------+---------------+---------------|
	| connected  | 5             | 5             |
	| ebgp       | 1000          | 100           |
	| ibgp       | 1             |               |
	| static     | 3             | 3             |
	| Totals     | 1009          | 108           |

	RIB maximum IPv6 routes(maximum/threshold): 200/80%

	Table: mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| Totals     | 0             |
	Table: color-mpls-nh

	| Protocol   | IPv4 Routes   |
	|------------+---------------|
	| Totals     | 0             |
	Table: color-mpls-nh-ipv6

	| Protocol   | IPv6 Routes   |
	|------------+---------------|
	| Totals     | 0             |
	Table: mpls-nh-ipv6

	| Protocol   | IPv6 Routes   |
	|------------+---------------|
	| Totals     | 0             |

	Table: multicast-ipv4-rpf, RPF check mode: intact

	| Protocol   | IPv4 Unicast Routes   | IPv4 Multicast Routes   |
	|------------+-----------------------+-------------------------|
	| connected  | 5                     |                         |
	| Totals     | 5                     | 0                       |

	Table: ipv4-flowspec, ipv6-flowspec

	| Protocol   | IPv4 Flows   | IPv6 Flows   |
	|------------+--------------+--------------|
	| Totals     | 0            | 0            |


.. **Help line:** show route summary


**Command History**

+---------+------------------------------------------------+
| Release | Modification                                   |
+=========+================================================+
| 5.1.0   | Command introduced                             |
+---------+------------------------------------------------+
| 11.5    | Added installed RSVP routes                    |
+---------+------------------------------------------------+
| 13.0    | Added IPv4 and IPv6 FlowSpec tables            |
+---------+------------------------------------------------+
| 16.1    | Added All filter                               |
+---------+------------------------------------------------+
| 16.1    | Extended support for Multicast RPF             |
+---------+------------------------------------------------+
| 18.1    | Added support for mpls color in ipv4 and ipv6  |
+---------+------------------------------------------------+
| 19.1    | Added support for Access protocol (DHCP/RA)    |
+---------+------------------------------------------------+
| 19.2    | Added per-vrf IPv4 and IPv6 max prefixes limit |
+---------+------------------------------------------------+
