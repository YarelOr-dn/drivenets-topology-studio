run ping
--------

**Minimum user role:** viewer

The ping command checks the accessibility of a destination interface. It uses a series of Internet Control Message Protocol (ICMP) Echo messages to determine whether or not the remote host is active, the round-trip delay in the communication with the host, and packet loss.

**Command syntax: run ping [dest-ip \| host-name]** vrf [vrf-name] source-interface [source-interface] interval [interval] size [size] count [count] dscp [dscp] df

**Command mode:** operation

**Note**

- The NCC handles ICMP packets. Therefore, ping to a remote host should be done from the NCC and not from the NCPs.

- All VRFs in the system are listed and made available, including the 4 system-default VRFs (default, mgmt0, mgmt-ncc-0 and mgmt-ncc-1). Unless a valid VRF is explicitly specified, the default VRF is used.

- The run ping command may include the source-interface. When a VRF is specified, only relevant source-interfaces attached to that VRF will be listed under it and made available. Otherwise, only interfaces under the default VRF are listed.

..
	- The ping command is one-line format. meaning - all parameters can be entered on the same line

		- dscp - ipv4/6 dscp value

		- Count - number or probe sequences per command

		- Size - ICMP payload

   		- Interval - resolution of 0.001 seconds

		- Df - don't fragment - a flag which specifies that outgoing packet shouldn't be fragmented and should be sent as is with original size. If size exceeds the egress interface mtu, then the packet will be dropped, by default, fragmentation is performed automatically. This option is only valid for IPv4 addresses.

	- By default source-address should be assigned based on RIB resolution of egress-interface towards the destination

	- If ping is initiated towards BGP-VPN prefix, then a random source-address will be assigned based on any attached UP interface with configured IP address inside the VRF. If no interface is attached, error message should be printed stating: "Cannot assign source address"

	- DNS resolution for ping command requested with host-name address within a VRF is done per system based on DNS servers priorities

	- If the IP destination address is a Link-Local address, then an applicable source interface will be chosen and link-local source address will be used (or retrieved from source-interface). If the IP destination address is a Global Unicast address, then an applicable source interface will be chosen and a global unicast source address will be used (or retrieved from source-interface)


.. **Help line:** run ICMP ping request


**Parameter table**

The following are the parameters that you can use for the ping command:

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                                                                  | Range                                               | Default |
+==================+==============================================================================================================================================================================================================+=====================================================+=========+
| dest-ip          | The IPv4/IPv6 address of the target host to ping                                                                                                                                                             | A.B.C.D                                             | \-      |
|                  |                                                                                                                                                                                                              | x:x::x:x                                            |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| host-name        | The name of the target host to ping                                                                                                                                                                          | String                                              | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| vrf-name         | The name of the target VRF                                                                                                                                                                                   | String                                              | default |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| source-interface | Sends the ping packets with the defined IP address of the source interface                                                                                                                                   | ge<interface speed>-<A>/<B>/<C>                     | \-      |
|                  |                                                                                                                                                                                                              |                                                     |         |
|                  |                                                                                                                                                                                                              | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>  |         |
|                  |                                                                                                                                                                                                              |                                                     |         |
|                  |                                                                                                                                                                                                              | bundle-<bundle id>                                  |         |
|                  |                                                                                                                                                                                                              |                                                     |         |
|                  |                                                                                                                                                                                                              | bundle-<bundle id>.<sub-interface id>               |         |
|                  |                                                                                                                                                                                                              |                                                     |         |
|                  |                                                                                                                                                                                                              | lo<lo-interface id>                                 |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| interval         | Specifies the time in seconds between sending ping packets (resolution of 0.001 seconds)                                                                                                                     | 0.001..86,400                                       | 1       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| size             | Specifies the number of data bytes to be added to the ping packet                                                                                                                                            | 1..65507                                            | 56      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| count            | Specifies the number of ping packets that will be sent                                                                                                                                                       | 1..1,000,000                                        | 5       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| dscp             | The IPv4/IPv6 DSCP value                                                                                                                                                                                     | 0..56                                               | 0       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| df               | Do not fragment - a flag specifying that outgoing packets must not be fragmented. The packets will be sent in their original size. If the size exceeds the egress interface MTU, the packet will be dropped  | Boolean                                             | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+

The parameters can all be specified in the same command.

**Example**
::

	dnRouter# run ping 1.1.1.1
	dnRouter# run ping google.com
	dnRouter# run ping 2001:1234::1
	dnRouter# run ping 10.0.0.1 source-interface lo0
	dnRouter# run ping 1.1.1.1 count 200
	dnRouter# run ping 1.1.1.1 interval 2
	dnRouter# run ping 1.1.1.1 size 1500
	dnRouter# run ping 1.1.1.1 interval 2 size 1000 dscp 40
	dnRouter# run ping 1.1.1.1 vrf mgmt0 count 20
	dnRouter# run ping 1.1.1.1 vrf mgmt-ncc-0 count 20
	dnRouter# run ping 1.1.1.1 vrf mgmt-ncc-1 source-interface mgmt-ncc-1 size 600
	dnRouter# run ping 1.1.1.1 vrf MyVrf1 df


**Command History**

+---------+----------------------------------------------------------------------------------------+
| Release | Modification                                                                           |
+=========+========================================================================================+
| 5.1.0   | Command introduced                                                                     |
+---------+----------------------------------------------------------------------------------------+
| 11.0    | Removed VRF filter, added option to ping a host-name, dscp, and option to not fragment |
+---------+----------------------------------------------------------------------------------------+
| 13.0    | Updated interval parameter values                                                      |
+---------+----------------------------------------------------------------------------------------+
| 13.1    | Added support for host VRF                                                             |
+---------+----------------------------------------------------------------------------------------+
| 13.3    | Updated interval parameter values from 0.1 seconds to 0.001 seconds                    |
+---------+----------------------------------------------------------------------------------------+
| 16.1    | Removed egress-interface knob                                                          |
+---------+----------------------------------------------------------------------------------------+
