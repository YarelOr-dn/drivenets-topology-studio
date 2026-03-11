vrf protocols bgp route-distinguisher
-------------------------------------

**Command syntax: route-distinguisher [route-distinguisher]**

**Description:** Set the route distinguisher for BGP as part VPN service

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-network-services)# vrf customer_vrf_1
	dnRouter(cfg-network-services-vrf)# protocols
	dnRouter(cfg-network-services-vrf-protocols)# bgp 65000
	dnRouter(cfg-vrf-protocols-bgp)# route-distinguisher 56335:1

	dnRouter(cfg-vrf-protocols-bgp)# no route-distinguisher

**Command mode:** config

**TACACS role:** operator

**Note:**

route-distinguisher is a mandatory parameter for l3vpn vrf instance

route-distinguisher must be **different** between different vrf

the "no route-distinguisher" remove the route-distinguisher in use.

**Help line:** Set the route distinguisher for BGP as part VPN service

**Parameter table:**

+---------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter           | Values                               | Description                                                                                                                                             |
+=====================+======================================+=========================================================================================================================================================+
| route-distinguisher | Type0:                               | as-number-short: 0.(2^16 -1)                                                                                                                            |
|                     |                                      |                                                                                                                                                         |
|                     | <[as-number-short]:[id-long]>        | as-number-long: (2^16).(2^32 -1)                                                                                                                        |
|                     |                                      |                                                                                                                                                         |
|                     | Type1:                               | id-short: 0.(2^16 -1)                                                                                                                                   |
|                     |                                      |                                                                                                                                                         |
|                     | <[as-number-short]**l**: [id-short]> | id-long: 0.(2^32 -1)                                                                                                                                    |
|                     |                                      |                                                                                                                                                         |
|                     | <[as-number-short]**L**:[id-short]>  | ipv4-address: A.B.C.D                                                                                                                                   |
|                     |                                      |                                                                                                                                                         |
|                     | <[as-number-long]:[id-short]>        | Note: using [as-number-short]**l** or [as-number-short]**L** will code as-number-short number in a 32bit field resulting in a Type1 route-distinguisher |
|                     |                                      |                                                                                                                                                         |
|                     | Type2:                               |                                                                                                                                                         |
|                     |                                      |                                                                                                                                                         |
|                     | <[ipv4-address]>:[id-short]>         |                                                                                                                                                         |
+---------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
