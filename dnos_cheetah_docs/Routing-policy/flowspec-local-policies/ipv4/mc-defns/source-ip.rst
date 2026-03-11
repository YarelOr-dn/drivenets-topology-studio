routing-policy flowspec-local-policies ipv4 match-class src-ip
--------------------------------------------------------------

**Minimum user role:** operator

Configures the src-ip as a match criteria of this traffic class. For the match to be made, all criteria must match.

**Command syntax: src-ip [src-ip]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Parameter table**

+-----------+----------------------------+-----------+---------+
| Parameter | Description                | Range     | Default |
+===========+============================+===========+=========+
| src-ip    | Source IPv4 address prefix | A.B.C.D/x | \-      |
+-----------+----------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# src-ip 192.168.10.20
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove the src-ip from the match class:
::

    dnRouter(cfg-flp-ipv4-mc)# no src-ip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
