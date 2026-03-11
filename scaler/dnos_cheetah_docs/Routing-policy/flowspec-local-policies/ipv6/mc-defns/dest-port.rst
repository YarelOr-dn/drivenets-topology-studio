routing-policy flowspec-local-policies ipv6 match-class dest-ports
------------------------------------------------------------------

**Minimum user role:** operator

Configures the destination port as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: dest-ports [dest-ports]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+------------+--------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                  | Range   | Default |
+============+==============================================================+=========+=========+
| dest-ports | Destination port range or a specific destination port value. | 0-65535 | \-      |
+------------+--------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# dest-ports 200-250
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the dest-ports from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no dest-ports

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
