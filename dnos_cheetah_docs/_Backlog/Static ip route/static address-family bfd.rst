static address-family bfd
-------------------------

You can use the following command to enter the BFD configuration level for BFD protection of a static route. A BFD session is created when bfd-nexthop is configured and enabled, and nexthop is used by at least one static route of the same type (single-hop/multi-hop). When a static route nexthop is protected by BFD, it is valid only when BFD is up.

To configure BFD protection of a Static route:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols static address-family

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# bfd
	dnRouter(cfg-static-ipv4-bfd)#


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# bfd
	dnRouter(cfg-static-ipv6-bfd)#


**Removing Configuration**

To remove BFD protection for the static route:
::

	dnRouter(cfg-protocols-static-ipv4)# no bfd
	dnRouter(cfg-protocols-static-ipv6)# no bfd

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+