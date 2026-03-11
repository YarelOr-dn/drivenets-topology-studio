protocols isis instance address-family ipv6-unicast ti-fast-reroute strict-spf-protection level level-1
-------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set if segment-routing can utilize the TI-LFA path for the protection of strict-spf prefix-sids:

**Command syntax: strict-spf-protection level level-1 [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast ti-fast-reroute

**Note**

- If the level is not specified, set for all isis supported levels.

- Level-1-2 settings are the default of per level behavior.

**Parameter table**

+-------------+---------------------------+--------------+---------+
| Parameter   | Description               | Range        | Default |
+=============+===========================+==============+=========+
| admin-state | configuration for level-1 | | enabled    | \-      |
|             |                           | | disabled   |         |
+-------------+---------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# strict-spf-protection level level-1 enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# ti-fast-reroute
    dnRouter(cfg-inst-afi-ti-frr)# strict-spf-protection level level-1 enabled


**Removing Configuration**

To revert the strict-spf-protection to the default value:
::

    dnRouter(cfg-inst-afi-ti-frr)# no level level-1 strict-spf-protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
