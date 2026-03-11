protocols static
-----------------

**Minimum user role:** operator

Routers forward packets using either route information from route table entries that you manually configure or the route information that is calculated using dynamic routing algorithms.  You can supplement dynamic routes with static routes where appropriate. Static routes are useful in environments where network traffic is predictable and where the network design is simple and for specifying a gateway of last resort (a default router to which all unroutable packets are sent).

To configure static routes you need to enter static configuration mode. To enter the static route configuration hierarchy:

**Command syntax: static**

**Command mode:** config

**Hierarchies**

- protocols

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)#

**Removing Configuration**

To remove all static route configurations:
::

	dnRouter(cfg-protocols)# no static


.. **Help line:** static route configuration

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+