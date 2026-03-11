routing-policy flowspec-local-policies ipv4 match-class tcp-flag
----------------------------------------------------------------

**Minimum user role:** operator

To add an optional description for the match class:

**Command syntax: tcp-flag [tcp-flag]** [, tcp-flag, tcp-flag]

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

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
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# tcp-flag syn,ack
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove the tcp-flag from the match-class:
::

    dnRouter(cfg-flp-ipv4-mc)# no tcp-flag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
