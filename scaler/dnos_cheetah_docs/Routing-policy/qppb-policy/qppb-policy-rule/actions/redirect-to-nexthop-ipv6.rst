routing-policy qppb-policy rule actions redirect-to-nexthop-ipv6
----------------------------------------------------------------

**Minimum user role:** operator

When the rule is matched the redirect-to-next-hop-ipv6 action will direct the matching traffic to the specified IPv6 destination.

To create a set action:

**Command syntax: redirect-to-nexthop-ipv6 [redirect-to-nexthop-ipv6]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+--------------------------+-------------------------------+----------+---------+
| Parameter                | Description                   | Range    | Default |
+==========================+===============================+==========+=========+
| redirect-to-nexthop-ipv6 | ipv6 redirect nexthop address | X:X::X:X | \-      |
+--------------------------+-------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) redirect-to-nexthop-ipv6 232:22::19:8
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)


**Removing Configuration**

To remove the redirect-to-next-hop-ipv6 action
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)# no redirect-to-nexthop-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
