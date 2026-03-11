run traceroute
--------------

**Minimum user role:** viewer

The run traceroute command displays the route that packets take to the specified destination address. When enabled, the router sends out a number of probes (UDP packets) set by the count parameter to the destination IP. This command is useful to locate points of failure in the network.

**Command syntax: run traceroute [dest-ip \| host-name]** vrf [vrf-name] source-interface [source-interface] dscp [dscp] max-hops [max-hops] dns-resolve df

**Command mode:** operation

**Note**

- The NCC handles ICMP packets. Therefore, traceroute to a remote host should be done from the NCC and not from the NCPs.

.. - The traceroute command is one-line format. meaning - all parameters can be entered on the same line

	 - run traceroute [dest-ip]source-interface [source-interface] - The traceroute packet should be sent with the defined ip address of the source interface.

	 - When using dns-resolve, we should remove the "-n" option

	 - Any VRF in the system will be listed and made available, including the four system-default VRFs (default, mgmt0, mgmt-ncc-0 and mgmt-ncc-1). Unless a valid VRF is explicitly specified, the default VRF will be used

	 - The run traceroute command may include source-interface. When a VRF is specified, only relevant source-interfaces attached to that VRF will be listed under it and made available. Otherwise, only interfaces under the default VRF will be listed

	 - By default, source-address should be assigned based on RIB resolution of egress-interface towards the destination

	 - If traceroute is initiated towards BGP-VPN prefix, then a random source-address will be assigned based on any attached UP interface with configured IP address inside the VRF. If no interface is attached, error message should be printed stating: "Cannot assign source address"

	 - DNS resolution for traceroute command requested with host-name address within a VRF is done per system based on DNS servers priorities

	 - If the IP destination address is a Link-Local address, then an applicable source interface will be chosen and link-local source address will be used (or retrieved from source-interface). If the IP destination address is Global Unicast address, then an applicable source interface will be chosen and global unicast source address will be used (or retrieved from source-interface)

**Parameter table**

The following are the parameters for this command:

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                                                                  | Range                                              | Default |
+==================+==============================================================================================================================================================================================================+====================================================+=========+
| dest-ip          | The IPv4 or IPv6 address of the remote host to trace                                                                                                                                                         | x.x.x.x                                            | \-      |
|                  |                                                                                                                                                                                                              | x:x::x:x                                           |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| host-name        | The name of the target host to trace                                                                                                                                                                         | String                                             | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| vrf-name         | The name of the target VRF                                                                                                                                                                                   | String                                             | default |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| source-interface | Sends the traceroute packets with the defined IP address of the source interface                                                                                                                             | ge<interface speed>-<A>/<B>/<C>                    | \-      |
|                  |                                                                                                                                                                                                              |                                                    |         |
|                  |                                                                                                                                                                                                              | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |         |
|                  |                                                                                                                                                                                                              |                                                    |         |
|                  |                                                                                                                                                                                                              | bundle-<bundle id>                                 |         |
|                  |                                                                                                                                                                                                              |                                                    |         |
|                  |                                                                                                                                                                                                              | bundle-<bundle id>.<sub-interface id>              |         |
|                  |                                                                                                                                                                                                              |                                                    |         |
|                  |                                                                                                                                                                                                              | lo<lo-interface id>                                |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| dscp             | The IPv4/IPv6 DSCP value                                                                                                                                                                                     | 0..56                                              | 0       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| max-hops         | The maximum number of hops that the trace packet should cross before timeout                                                                                                                                 | 1..255                                             | 30      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| dns-resolve      | Queries the DNS server to resolve the IP addresses of the next hops. By default, only the IP address is returned, unless dns-resolve is explicitly specified                                                 | \-                                                 | \-      |
|                  | Note, using the dns-resolve option may significantly slow down the response time                                                                                                                             |                                                    |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| df               | Do not fragment - a flag specifying that outgoing packets must not be fragmented. The packets will be sent in their original size. If the size exceeds the egress interface MTU, the packet will be dropped  | Boolean                                            | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+

The parameters can all be specified in the same command.

**Example**
::

	dnRouter# run traceroute 1.1.1.1
	dnRouter# run traceroute 2001:1234::1
	dnRouter# run traceroute source-interface lo0
	dnRouter# run traceroute 1.1.1.1 max-hops 2
	dnRouter# run traceroute 1.1.1.1 dscp 4
	dnRouter# run traceroute 1.1.1.1 dns-resolve
	dnRouter# run traceroute 1.1.1.1 vrf mgmt0
	dnRouter# run traceroute 1.1.1.1 vrf mgmt-ncc-0 max-hops 9
	dnRouter# run traceroute 1.1.1.1 vrf mgmt-ncc-1 source-interface mgmt-ncc-1
	dnrouter# run traceroute google.com vrf MyVrf1

.. **Help line:** run traceroute request

**Command History**

+---------+------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                               |
+=========+============================================================================================================+
| 5.1.0   | Command introduced                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------+
| 10.0    | Removed dns-resolve option                                                                                 |
+---------+------------------------------------------------------------------------------------------------------------+
| 11.0    | Removed VRF filter, added option to trace a host-name, added dscp dns-resolve, and option to not fragment  |
+---------+------------------------------------------------------------------------------------------------------------+
| 11.2    | Removed size from the syntax                                                                               |
+---------+------------------------------------------------------------------------------------------------------------+
| 13.1    | Added support for host VRF                                                                                 |
+---------+------------------------------------------------------------------------------------------------------------+
| 16.1    | Removed egress-interface knob                                                                              |
+---------+------------------------------------------------------------------------------------------------------------+
