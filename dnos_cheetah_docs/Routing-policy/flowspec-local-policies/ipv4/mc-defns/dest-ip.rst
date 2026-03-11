routing-policy flowspec-local-policies ipv4 match-class dest-ip
---------------------------------------------------------------

**Minimum user role:** operator

To configure the dest-ip as a match criteria of this match class. All criteria must match, for the match to be made.

**Command syntax: dest-ip [dest-ip]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Parameter table**

+-----------+---------------------------------+-----------+---------+
| Parameter | Description                     | Range     | Default |
+===========+=================================+===========+=========+
| dest-ip   | Destination IPv4 address prefix | A.B.C.D/x | \-      |
+-----------+---------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# dest-ip 192.168.10.20
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove the dest-ip from the match class:
::

    dnRouter(cfg-flp-ipv4-mc)# no dest-ip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
