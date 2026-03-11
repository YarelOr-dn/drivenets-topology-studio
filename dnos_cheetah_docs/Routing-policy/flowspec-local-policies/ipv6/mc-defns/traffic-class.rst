routing-policy flowspec-local-policies ipv6 match-class traffic-class
---------------------------------------------------------------------

**Minimum user role:** operator

Configures the Traffic-Class as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: traffic-class [traffic-class]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+---------------+---------------+-------+---------+
| Parameter     | Description   | Range | Default |
+===============+===============+=======+=========+
| traffic-class | Traffic class | 0-63  | \-      |
+---------------+---------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# traffic-class 45
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the traffic-class from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no traffic-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
