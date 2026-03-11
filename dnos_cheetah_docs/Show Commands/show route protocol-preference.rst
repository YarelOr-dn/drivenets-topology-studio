show route protocol-preference
------------------------------

**Minimum user role:** viewer

To display administrative distance and FIB installation priority per protocol:



**Command syntax: show route protocol-preference** vrf [vrf-name]

**Command mode:** operational

**Note:**

* When vrf name not specified, default vrf will be shown as default.

**Parameter table:**

+---------------+---------------------------------------------------+------------------------+---------------+
| Parameter     | Values                                            | Range                  | Default       |
+===============+===================================================+========================+===============+
| vrf-name      | String, a configured vrf name                     | 1..255 characters      | default       |
+---------------+---------------------------------------------------+------------------------+---------------+


**Example**
::

	dnRouter# show route protocol-preference

	VRF: default
	| Protocols     | Administrative-distance   | Instance name    |
	+---------------+---------------------------+------------------+
	| Access-High   | 10                        |                  |
	| Access-Medium | 11                        |                  |
	| Access-Low    | 12                        |                  |
	| Connected     | 0                         |                  |
	| RSVP          | 100                       |                  |
	| SR-TE         | 103                       |                  |
	| LDP           | 105                       |                  |
	| Static        | 1(default)                |                  |
	| ISIS-SR       | 107                       | INST_1           |
	| ISIS          | 114                       | INST_2           |
	| ISIS          | 116                       | INST_1           |
	| BGP-External  | 20                        |                  |
	| BGP-Internal  | 200                       |                  |

	| Protocols                | Install   |
	+--------------------------+-----------+
	| Access                   | High      |
	| Connected                | High      |
	| Static                   | High      |
	| RSVP                     | High      |
	| SR-TE                    | Medium    |
	| LDP                      | Medium    |
	| OSPF                     | Medium    |
	| OSPF-SR                  | Medium    |
	| ISIS-SR                  | Medium    |
	| ISIS                     | Medium    |
	| BGP ipv4 labeled-unicast | Medium    |
	| BGP ipv6 labeled-unicast | Medium    |
	| BGP ipv4 unicast         | Low       |
	| BGP ipv6 unicast         | Low       |
	| BGP ipv4 vpn             | Low       |
	| BGP ipv6 vpn             | Low       |
	| BGP link-state           | Low       |


	dnRouter# show route protocol-preference

	VRF: default
	| Protocols     | Administrative-distance   | Instance name    |
	+---------------+---------------------------+------------------+
	| Access-High   | 10                        |                  |
	| Access-Medium | 11                        |                  |
	| Access-Low    | 12                        |                  |
	| Connected     | 0                         |                  |
	| RSVP          | 100                       |                  |
	| SR-TE         | 103                       |                  |
	| LDP           | 105                       |                  |
	| Static        | 1(default)                |                  |
	| OSPF          | 110                       | INST_A           |
	| OSPF          | 114                       | INST_B           |
	| OSPF-SR       | 107                       | INST_A           |
	| BGP-External  | 20                        |                  |
	| BGP-Internal  | 200                       |                  |

	| Protocols                | Install   |
	+--------------------------+-----------+
	| Access                   | High      |
	| Connected                | High      |
	| Static                   | High      |
	| RSVP                     | High      |
	| SR-TE                    | Medium    |
	| LDP                      | Medium    |
	| OSPF                     | Medium    |
	| OSPF-SR                  | Medium    |
	| ISIS-SR                  | Medium    |
	| ISIS                     | Medium    |
	| BGP ipv4 labeled-unicast | Medium    |
	| BGP ipv6 labeled-unicast | Medium    |
	| BGP ipv4 unicast         | Low       |
	| BGP ipv6 unicast         | Low       |
	| BGP ipv4 vpn             | Low       |
	| BGP ipv6 vpn             | Low       |
	| BGP link-state           | Low       |


	dnRouter# show route protocol-preference vrf VRF_A

	VRF: VRF_A
	| Protocol                          | Administrative-distance          | Instance name     |
	+-----------------------------------+----------------------------------+-------------------+
	| Connected                         |                                0 |                   |
	| Static                            |                       1(default) |                   |
	| BGP-External                      |                               15 |                   |
	| BGP-Internal                      |                              195 |                   |

	| Protocol                          | Install-priority   |
	+-----------------------------------+--------------------+
	| Connected                         | High               |
	| Static                            | High               |
	| RSVP                              | High               |
	| LDP                               | Medium             |
	| OSPF                              | Medium             |
	| ISIS                              | Medium             |
	| BGP ipv4 labeled-unicast          | Medium             |
	| BGP ipv6 labeled-unicast          | Medium             |
	| BGP ipv4 unicast                  | Low                |
	| BGP ipv6 unicast                  | Low                |
	| BGP ipv4 vpn                      | Low                |
	| BGP ipv6 vpn                      | Low                |
	| BGP link-state                    | Low                |


**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 10.0    | Command introduced                          |
+---------+---------------------------------------------+
| 16.2    | Added ISIS High-Priority Tagged             |
+---------+---------------------------------------------+
| 17.0    | Added support for specific vrf name         |
+---------+---------------------------------------------+
| 19.1    | Added support for Access protocol (DHCP/RA) |
+---------+---------------------------------------------+