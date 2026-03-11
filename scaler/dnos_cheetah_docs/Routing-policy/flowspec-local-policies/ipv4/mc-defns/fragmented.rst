routing-policy flowspec-local-policies ipv4 match-class fragmented
------------------------------------------------------------------

**Minimum user role:** operator

Configures the fragmented packets as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: fragmented**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# fragmented
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove fragmented from the match class:
::

    dnRouter(cfg-flp-ipv4-mc)# no fragmented

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
