system management vrf static address-familiy
--------------------------------------------

**Minimum user role:** operator

To configure static routes for out-of-band management mgmt vrfs. These vrfs are not part of any traffic forwarding vrf:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- system management static


**Note**

- Notice the change in prompt

.. - "no [address-family]" removes all static routes from the specified address-family

**Parameter table**

+----------------+----------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                | Range | Default |
+================+============================================================================+=======+=========+
| address-family | Enters the address-family for which to configure management static routes. | IPv4  | \-      |
|                |                                                                            | IPv6  |         |
+----------------+----------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static 
	dnRouter(cfg-system-mgmt-vrf-static)# address-family ipv4
	dnRouter(cfg-mgmt-vrf-static-ipv4)#

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static 
	dnRouter(cfg-system-mgmt-vrf-static)# address-family ipv6
	dnRouter(cfg-mgmt-vrf-static-ipv6)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-mgmt-vrf-static)# no address-family ipv4 


**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Command syntax updated |
+---------+------------------------+


