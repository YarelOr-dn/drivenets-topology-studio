static address-family
---------------------

**Minimum user role:** operator

To static route configuration for an address-family:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- protocols static

**Parameter table**

+-------------------+--------------------------------------------+-----------------+-------------+
|                   |                                            |                 |             |
| Parameter         | Description                                | Range           | Default     |
+===================+============================================+=================+=============+
|                   |                                            |                 |             |
| address-family    | Enter address-family configuration mode    | IPv4-unicast    | \-          |
|                   |                                            |                 |             |
|                   |                                            | IPv6-unicast    |             |
+-------------------+--------------------------------------------+-----------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)#
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)#

**Removing Configuration**

To delete all address-family static routes:
::

	dnRouter(cfg-protocols-static)# no address-family ipv4-unicast
	dnRouter(cfg-protocols-static)# no address-family ipv6--unicast

.. **Help line:** static route address family

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+