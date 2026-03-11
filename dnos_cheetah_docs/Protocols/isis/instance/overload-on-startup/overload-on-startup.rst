protocols isis instance overload on-startup
-------------------------------------------

**Minimum user role:** operator

When a router starts, it takes time until the routing tables are converged to align with network forwarding. In cases where BGP unicast routes are forwarded over IS-IS reachability, there is a need to wait for BGP convergence before advertising itself as a valid transit router. You can define the amount of time IS-IS is considered to be overloaded after BGP convergence has completed, by setting the wait-for-bgp timer and / or an interval period (there is an additional *bgp-delay* timer after BGP has converged).

To enter overload on-startup configuration level:


**Command syntax: overload on-startup**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- The *interval* timer will always take precedence even if wait-for-bgp is set. When the interval expires, the system will no longer be considered in overload.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# overload on-startup
    dnRouter(cfg-isis-inst-overload)#


**Removing Configuration**

::

    dnRouter(cfg-protocols-isis)# no overload on-startup

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
