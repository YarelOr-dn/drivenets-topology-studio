protocols isis instance address-family ipv6-unicast ti-fast-reroute admin-state level level-2
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable ti-lfa fast-reroute:

**Command syntax: admin-state level level-2 [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast ti-fast-reroute

**Note**

- ti-fast-reroute cannot be enabled if isis fast-reroute is enabled for the same address-family and level.

**Parameter table**

+-------------+---------------------------+--------------+---------+
| Parameter   | Description               | Range        | Default |
+=============+===========================+==============+=========+
| admin-state | configuration for level-2 | | enabled    | \-      |
|             |                           | | disabled   |         |
+-------------+---------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# admin-state level level-2 enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# admin-state level level-2 enabled


**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no admin-state level level-2 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
