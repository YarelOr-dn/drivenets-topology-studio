routing-policy policy rule set resolve-nexthop-in
-------------------------------------------------

**Minimum user role:** operator

When set on a given BGP route path. It is required to resolve the path nexthop in a specific VRF RIB table.

**Command syntax: set resolve-nexthop-in [vrf-name]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-----------+-------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                 | Range            | Default |
+===========+=============================================================+==================+=========+
| vrf-name  | Require to resolve path nexthop in a specific vrf rib table | | string         | \-      |
|           |                                                             | | length 1-255   |         |
+-----------+-------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# set resolve-nexthop-in VRF_A


**Removing Configuration**

To remove set protocols criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no set resolve-nexthop-in

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
