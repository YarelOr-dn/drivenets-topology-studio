protocols isis instance address-family ipv4-unicast propagate level2-to-level1 policy
-------------------------------------------------------------------------------------

**Minimum user role:** operator

By default, all level-1 routes propagate into level-2. Use this command to filter the routes that propagate from level-1 to level-2, or to enable route leaking from level-2 to level-1. To do both, explicitly set the command twice, once for each direction. Note that using a policy is mandatory with this command; the policy limits the number of route that are propagated or leaked.

To propagate routes between levels:

**Command syntax: propagate level2-to-level1 policy [policy-name]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**
- "Only the following commands can be used in the propagation attachment points; other match/set statements will be ignored:"
.. - "policy match ip prefix"
.. - "policy match tag"
.. - "policy set tag"
- Routes can propagate from level-1 to level-2 and from level-2 to level-1 at the same time. They cannnot propagate between same levels.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| policy-name | Enter an existing policy that lists the routes that will be propagated or        | | string         | \-      |
|             | leaked. Only "policy match ip prefix" can be used in the propagation attachment  | | length 1-255   |         |
|             | points. Other match / set statements will be ignored.                            |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# redistribute static
    dnRouter(cfg-isis-inst-afi)# propagate level2-to-level1 policy LEAK_FILTER


**Removing Configuration**

To stop level-2 into level-1 propagation filtering:
::

    dnRouter(cfg-isis-inst-afi)# no propagate level2-to-level1

**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 14.0    | Command introduced     |
+---------+------------------------+
| 15.0    | Updated command syntax |
+---------+------------------------+
