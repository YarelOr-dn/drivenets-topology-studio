vrf protocols bgp address-family import-vpn route-target
--------------------------------------------------------

**Command syntax: import-vpn route-target [route-target],** [route-target], .

**Description:** Enable import of routes with route-target specified to the vrf tables

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# route-distinguisher 56335:1
	dnRouter(cfg-vrf-protocols-bgp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 49844:20, 49844:30
	dnRouter(cfg-protocols-bgp-afi)# import-vpn route-target 49844:40

	dnRouter(cfg-bgp-neighbor-afi)# no import-vpn route-target 49844:50

**Command mode:** config

**TACACS role:** operator

**Note:**

can import multiple different route-target tagged routes.

no command stops importing routes with the specified route-target

**Help line:** Enable import of routes with route-target specified to the vrf tables

**Parameter table:**

+--------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter    | Values                               | Description                                                                                                                                             |
+==============+======================================+=========================================================================================================================================================+
| route-target | Type0:                               | as-number-short: 0.(2^16 -1)                                                                                                                            |
|              |                                      |                                                                                                                                                         |
|              | <[as-number-short]:[id-long]>        | as-number-long: (2^16).(2^32 -1)                                                                                                                        |
|              |                                      |                                                                                                                                                         |
|              | Type1:                               | id-short: 0.(2^16 -1)                                                                                                                                   |
|              |                                      |                                                                                                                                                         |
|              | <[as-number-short]**l**: [id-short]> | id-long: 0.(2^32 -1)                                                                                                                                    |
|              |                                      |                                                                                                                                                         |
|              | <[as-number-short]**L**:[id-short]>  | ipv4-address: A.B.C.D                                                                                                                                   |
|              |                                      |                                                                                                                                                         |
|              | <[as-number-long]:[id-short]>        | Note: using [as-number-short]**l** or [as-number-short]**L** will code as-number-short number in a 32bit field resulting in a Type1 route-distinguisher |
|              |                                      |                                                                                                                                                         |
|              | Type2:                               |                                                                                                                                                         |
|              |                                      |                                                                                                                                                         |
|              | <[ipv4-address>:[id-short]>          |                                                                                                                                                         |
+--------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
