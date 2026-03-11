protocols static
----------------

**Minimum user role:** operator

Routers forward packets using either route information from route table entries that you manually configure or the route information that is calculated using dynamic routing algorithms. You can supplement dynamic routes with static routes where appropriate. Static routes are useful in environments where network traffic is predictable and where the network design is simple and for specifying a gateway of last resort (a default router to which all unroutable packets are sent).
To configure static routes, enter the static configuration hierarchy:

**Command syntax: static**

**Command mode:** config

**Hierarchies**

- protocols
- network-services vrf instance protocols

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)#


**Removing Configuration**

To remove all static config per vrf instance:
::

    dnRouter(cfg-vrf-inst-protocols)# no static

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
