routing-policy flowspec-local-policies ipv6 match-class dest-ip
---------------------------------------------------------------

**Minimum user role:** operator

Configures the dest-ip as a match criteria of this match class. For the match to be made, all the criteriaa must match.

**Command syntax: dest-ip [dest-ip]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+-----------+---------------------------------+------------+---------+
| Parameter | Description                     | Range      | Default |
+===========+=================================+============+=========+
| dest-ip   | Destination IPv6 address prefix | X:X::X:X/x | \-      |
+-----------+---------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# dest-ip 1050::5:620:510c:357c
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the dest-ip from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no dest-ip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
