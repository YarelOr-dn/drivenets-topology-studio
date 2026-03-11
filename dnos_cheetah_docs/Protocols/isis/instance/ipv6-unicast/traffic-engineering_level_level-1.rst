protocols isis instance address-family ipv6-unicast traffic-engineering level level-1
-------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable traffic-engineering support in IS-IS level-1:


**Command syntax: traffic-engineering level level-1 [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**

- TE support is for either level 1 or level 2, even when the IS-IS router supports level-1-2. It cannot be enabled together with traffic-engineering support for level-2.

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | set TE support for Level-1 routing | | enabled    | \-      |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# traffic-engineering level level-1 enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no traffic-engineering level level-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
