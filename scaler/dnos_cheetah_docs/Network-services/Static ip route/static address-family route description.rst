static address-family route description
---------------------------------------

**Command syntax: route [ip-prefix] description [description]**

**Description:** Sets a description for the static route. The same route can have only one description, regardless of how many nexthop options it has

description is visible under "show config"

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# route 172.16.172.0/24 description route to cluster 1


	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# network-services
	dnRouter(cfg-netsrv)# vrf customer_vrf_1
	dnRouter(cfg-netsrv-vrf)# protocols
	dnRouter(cfg-netsrv-vrf-protocols)# static
	dnRouter(cfg-netsrv-vrf-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-netsrv-vrf-protocols-static-ipv6)# route 232:16::8:0/96 description MY_DESCRIPTION


	dnRouter(cfg-netsrv-vrf-protocols-static-ipv4)# no route 172.16.172.0/24 description

**Command mode:** config

**TACACS role:** operator

**Note:**

-  no command remove description

-  no command removes the static route from RIB, identified by target network and gateway.

**Help line:** static route configuration

**Parameter table:**

+-------------+-------------------------+---------------+----------------------------------------------+
| Parameter   | Values                  | Default value | notes                                        |
+=============+=========================+===============+==============================================+
| ip-prefix   | A.B.C.D/M,              |               | must comply with the relative address-family |
|             |                         |               |                                              |
|             | {ipv6 address format}/M |               | M: 0-32 for ipv4-address                     |
|             |                         |               |                                              |
|             |                         |               | M: 0-128 for ipv6-address                    |
+-------------+-------------------------+---------------+----------------------------------------------+
| description | string                  |               |                                              |
|             |                         |               |                                              |
|             | length 1..255           |               |                                              |
+-------------+-------------------------+---------------+----------------------------------------------+
