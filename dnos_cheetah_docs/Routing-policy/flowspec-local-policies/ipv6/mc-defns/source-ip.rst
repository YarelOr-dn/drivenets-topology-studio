routing-policy flowspec-local-policies ipv6 match-class src-ip
--------------------------------------------------------------

**Minimum user role:** operator

Configures the src-ip as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: src-ip [src-ip]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+-----------+----------------------------+------------+---------+
| Parameter | Description                | Range      | Default |
+===========+============================+============+=========+
| src-ip    | Source IPv6 address prefix | X:X::X:X/x | \-      |
+-----------+----------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# src-ip 1050::5:620:510c:357c
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the source-ipv6 from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no source-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
