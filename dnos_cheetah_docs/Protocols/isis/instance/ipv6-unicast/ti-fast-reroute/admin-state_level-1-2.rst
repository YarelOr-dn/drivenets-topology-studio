protocols isis instance address-family ipv6-unicast ti-fast-reroute admin-state
-------------------------------------------------------------------------------

**Minimum user role:** operator

To enable ti-lfa fast-reroute:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast ti-fast-reroute

**Note**

- ti-fast-reroute cannot be enabled if isis fast-reroute is enabled for the same address-family and level.

- If the level is not specified, set for all isis supported levels.

- Level-1-2 settings are the default of per level behavior.

**Parameter table**

+-------------+-----------------------------+--------------+----------+
| Parameter   | Description                 | Range        | Default  |
+=============+=============================+==============+==========+
| admin-state | configuration for level-1-2 | | enabled    | disabled |
|             |                             | | disabled   |          |
+-------------+-----------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# admin-state enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# admin-state enabled


**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
