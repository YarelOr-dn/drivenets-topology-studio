routing-policy qppb-policy rule actions redirect-to-nexthop-ipv4
----------------------------------------------------------------

**Minimum user role:** operator

When the rule is matched the redirect-to-next-hop-ipv4 action will direct the matching traffic to the specified IPv4 destination.

To create a set action:

**Command syntax: redirect-to-nexthop-ipv4 [redirect-to-nexthop-ipv4]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+--------------------------+-------------------------------+---------+---------+
| Parameter                | Description                   | Range   | Default |
+==========================+===============================+=========+=========+
| redirect-to-nexthop-ipv4 | ipv4 redirect nexthop address | A.B.C.D | \-      |
+--------------------------+-------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) redirect-to-nexthop-ipv4 192.15.87.23
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)# no redirect-to-nexthop-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
