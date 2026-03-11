protocols isis instance address-family ipv6-unicast metric level level-1
------------------------------------------------------------------------

**Minimum user role:** operator

To configure a non-passive level-1 interface default metric value:

**Command syntax: metric level level-1 [metric]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**

- Level configuration is optional, if no level is set, impose for level-1-2. Any configuration for more specific level takes presedence.

- The default metric applies for non-passive interfaces only.

- Any interface level metric configuration in the relevant address-family, takes presedence over global address-family metric settings.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                      | Range      | Default |
+===========+==================================================================================+============+=========+
| metric    | If you do not specify level-1 and level-2 for level-1-2 ISs, then the same       | 1-16777215 | \-      |
|           | metric is set for both level-1 and level-2.                                      |            |         |
+-----------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# metric level level-1 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-isis-inst-afi)# no metric level level-1 20

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
