routing-policy flowspec-local-policies ipv6 match-class tcp-flag
----------------------------------------------------------------

**Minimum user role:** operator

Configures the tcp-flag as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: tcp-flag [tcp-flag]** [, tcp-flag, tcp-flag]

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+-----------+----------------+---------+---------+
| Parameter | Description    | Range   | Default |
+===========+================+=========+=========+
| tcp-flag  | TCP flags list | | syn   | \-      |
|           |                | | ack   |         |
|           |                | | urg   |         |
|           |                | | psh   |         |
|           |                | | rst   |         |
|           |                | | fin   |         |
+-----------+----------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# tcp-flag syn,ack
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the tcp-flag from the match-class:
::

    dnRouter(cfg-flp-ipv6-mc)# no tcp-flag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
