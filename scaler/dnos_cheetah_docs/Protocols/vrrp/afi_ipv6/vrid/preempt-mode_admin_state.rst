protocols vrrp interface address-family ipv6 vrid preempt-mode admin-state
--------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable preeempt mode for the VRRP group:

**Command syntax: preempt-mode admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv6 vrid
- network-services vrf instance protocols vrrp interface address-family ipv6 vrid

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | When activated enables preemption by a higher priority backup router of a lower  | | enabled    | enabled |
|             | priority master router                                                           | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# preempt-mode admin-state disabled


**Removing Configuration**

To return the preempt-mode admin-state to its default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no preempt-mode admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
