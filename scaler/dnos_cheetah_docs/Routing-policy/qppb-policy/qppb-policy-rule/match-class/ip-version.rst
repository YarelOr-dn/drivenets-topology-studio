routing-policy qppb-policy rule match-class ip-version
------------------------------------------------------

**Minimum user role:** operator

Define which ip version packets will be matched by the rule. Default behavior is match "any", i.e either IPv4 or IPv6 packets.

To Configure ip-version:

**Command syntax: ip-version [ip-version]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule match-class

**Note**

- default behavior is match "any", i.e either IPv4 or IPv6 packets

**Parameter table**

+------------+-------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                 | Range   | Default |
+============+=============================================================+=========+=========+
| ip-version | Define which ip version packets will be matched by the rule | | 4     | any     |
|            |                                                             | | 6     |         |
|            |                                                             | | any   |         |
+------------+-------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# match-class
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)# ip-version 4
    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)#


**Removing Configuration**

To remove the ip-version from the match-class
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-match-class)# no ip-version

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
