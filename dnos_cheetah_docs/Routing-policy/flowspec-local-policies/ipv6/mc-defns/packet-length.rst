routing-policy flowspec-local-policies ipv6 match-class packet-length
---------------------------------------------------------------------

**Minimum user role:** operator

Configures the packet-length as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: packet-length [packet-length]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+---------------+--------------------------------------------------------+---------+---------+
| Parameter     | Description                                            | Range   | Default |
+===============+========================================================+=========+=========+
| packet-length | Packet-length range or a specific packet length value. | 0-65535 | \-      |
+---------------+--------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# packet-length 2000-2500
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the packet-length from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no packet-length

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
