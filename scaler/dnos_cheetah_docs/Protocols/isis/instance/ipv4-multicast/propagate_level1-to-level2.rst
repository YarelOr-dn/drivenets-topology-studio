protocols isis instance address-family ipv4-multicast propagate level1-to-level2 policy
---------------------------------------------------------------------------------------

**Minimum user role:** operator

Propagate isis routes between levels.
Propagate level-1 into level-2 - By default all routes from level-1 will be propagated to level-2.
The command is used to filter propagation.


**Command syntax: propagate level1-to-level2 policy [policy]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Note**

- Only "policy match ip prefix" can be used in the propagation attachement points. Other match / set statements will be ignored.

**Parameter table**

+-----------+----------------------------------------------------+------------------+---------+
| Parameter | Description                                        | Range            | Default |
+===========+====================================================+==================+=========+
| policy    | Used to filter propagation from Level 1 to Level 2 | | string         | \-      |
|           |                                                    | | length 1-255   |         |
+-----------+----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# propagate level1-to-level2 policy L1_TO_L2_FILTER


**Removing Configuration**

To revert to default behavior, where all routes are propagated from level-1 to level-2:
::

    dnRouter(cfg-isis-inst-afi)# no propagate level1-to-level2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
