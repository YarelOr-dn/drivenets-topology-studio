segment-routing mpls path segment-list hop
------------------------------------------

**Minimum user role:** operator

The segment-list hop represents a single segment within the path. Each hop is associated with a specific label, a prefix-SID index, or a prefix-SID IPv4-address. You can configure up to 5 segments per segment-list.

To configure a segment-list hop:

**Command syntax: hop [hop-id] { label [label] | adjacency-sid [ipv4-address] | include prefix-sid index [index] | include prefix-sid {ipv4-address [ipv4-address] | ipv6-address [ipv6-address]} {spf|strict-spf|[flex-algo id]} }**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path segment-list

**Note**

Required validations:

- label must be within configured SRGB

- index must be within configured SRGB range

- ipv4-address must be a legal unicast ipv4 address, i.e not multicast of broadcast address.

- ipv6-address must be a legal global unicast ipv6 address.

.. - 'no hop <hop-id>' removes a specific hop from segment-list

.. - 'no hop' removes all configured hops from segment-list


**Parameter table:**

+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            |                                                                                                                                                                                                                                                                                                                                                                     |                                                    |             |
| Parameter                  | Description                                                                                                                                                                                                                                                                                                                                                         | Range                                              | Default     |
+============================+=====================================================================================================================================================================================================================================================================================================================================================================+====================================================+=============+
|                            |                                                                                                                                                                                                                                                                                                                                                                     |                                                    |             |
| hop-id                     | The hop identifier. You can configure up to 9   hops with IDs from 1 to 9.                                                                                                                                                                                                                                                                                          | 1..9                                               | \ -         |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            |                                                                                                                                                                                                                                                                                                                                                                     |                                                    |             |
| label                      | Set the label value for the associated hop (hop-id). The configured label value will be injected into the corresponding label on the policy label stack. For the first hop, the system will verify that the label can be resolved according to the local SRGB. No validation will be done for any other hop. That is, the label can be unrecognized by the network. | 256..1048575                                       | \ -         |
|                            |                                                                                                                                                                                                                                                                                                                                                                     |                                                    |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            | Configure an address for the hop local interface address. DNOS will resolve the address for the matching adjacency SID according to LSPDB. Address can be also be local node interface, which will enforce traffic via the interface                                                                                                                                |                                                    |             |
| adjacency-sid              |                                                                                                                                                                                                                                                                                                                                                                     | A.B.C.D                                            |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            | Configure an address for the hop. DNOS will resolve the address for the matching SID according to SR DB. The SPF or strict-SPF algorithm must be specified to support exact match.                                                                                                                                                                                  |                                                    |             |
| prefix-sid index           |                                                                                                                                                                                                                                                                                                                                                                     | 0..255999                                          |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            | Configure an address for the hop. DNOS will resolve the address for the matching SID according to SR DB. The SPF or strict-SPF algorithm must be specified to support exact match.                                                                                                                                                                                  |                                                    |             |
| prefix-sid ipv4-address    |                                                                                                                                                                                                                                                                                                                                                                     | A.B.C.D                                            |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            | Configure an address for the hop. DNOS will resolve the address for the matching SID according to SR DB. The SPF or strict-SPF algorithm must be specified to support exact match.                                                                                                                                                                                  |                                                    |             |
| prefix-sid ipv6-address    |                                                                                                                                                                                                                                                                                                                                                                     | X:X::X:X                                           |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            | Define which constraint-based shortest-path prefix-SID algorithm segment routing will use:                                                                                                                                                                                                                                                                          |                                                    |             |
| spf | strict-spf           | - Shortest Path First (SPF): This algorithm is the default behavior. The packet is forwarded along the well known ECMP-aware SPF algorithm employed by the IGPs. However, it is explicitly allowed for a midpoint router in the path to implement another forwarding based on local policy.                                                                         | SPF                                                | \ -         |
|                            | - Strict-SPF: This algorithm mandates that the packet be forwarded according to the ECMP-aware SPF algorithm and instructs any router in the path to ignore any possible local policy overriding the SPF decision. The SID advertised with the strict-SPF algorithm ensures that the path the packet is going to take is the expected, and not altered, SPF path.   |                                                    |             |
|                            |                                                                                                                                                                                                                                                                                                                                                                     | Strict-SPF - recommended to avoid routing loops    |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|                            |                                                                                                                                                                                                                                                                                                                                                                     |                                                    |             |
| flex-algo id               |  Define which constraint-based flexible algorithm algorithm segment routing will use to resolve sid                                                                                                                                                                                                                                                                 | 128..255                                           |             |
+----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protcols
	dnRouter(cfg-protocols)# segment-routing
	dnRouter(cfg-protocols-sr)# mpls
	dnRouter(cfg-protocols-sr-mpls)# path PATH_1
	dnRouter(cfg-sr-mpls-path)# segment-list 1
	dnRouter(cfg-mpls-path-sl)# hop 1 label 10000
	dnRouter(cfg-mpls-path-sl)# hop 2 prefix-sid include index 2
	dnRouter(cfg-mpls-path-sl)# hop 3 prefix-sid include ipv4-address 3.3.3.3 spf
	dnRouter(cfg-mpls-path-sl)# hop 4 prefix-sid include ipv4-address 4.4.4.4 strict-spf
	dnRouter(cfg-mpls-path-sl)# hop 5 prefix-sid include ipv4-address 5.5.5.5 128


**Removing Configuration**

To remove a specific hop or all configured hops from the segment-list:
::

	dnRouter(cfg-mpls-path-sl)# no hop 2
	dnRouter(cfg-mpls-path-sl)# no hop


.. **Help line:** Configure segment-list hop

**Command History**

+-----------+-------------------------------------+
| Release   | Modification                        |
+===========+=====================================+
|  15.0     | Command introduced                  |
+-----------+-------------------------------------+
|  17.0     | Add adjacency-sid hop option        |
+-----------+-------------------------------------+
|  18.0     | -Extended support to 9 hops         |
|           | -Added algorithm flex-algo id option|
+-----------+-------------------------------------+
|  18.2      | Added ipv6 support                 |
+-----------+-------------------------------------+