protocols isis instance address-family ipv4-multicast propagate level2-to-level1 policy
---------------------------------------------------------------------------------------

**Minimum user role:** operator

Propagate isis routes between levels.
Propagate level-2 into level-1 - By default no route is propagated from level-2 into level-1.
Use policy to control which routes will be propagated


**Command syntax: propagate level2-to-level1 policy [policy]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Note**

- Only "policy match ip prefix" can be used in the propagation attechement points. Other match / set statements will be ignored

**Parameter table**

+-----------+--------------------------------------+------------------+---------+
| Parameter | Description                          | Range            | Default |
+===========+======================================+==================+=========+
| policy    | Policy to filter allow leaked routes | | string         | \-      |
|           |                                      | | length 1-255   |         |
+-----------+--------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# propagate level2-to-level1 policy L2_TO_L1_FILTER


**Removing Configuration**

To stop level-2 to level-1 propagation:
::

    dnRouter(cfg-isis-inst-afi)# no propagate level2-to-level1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
