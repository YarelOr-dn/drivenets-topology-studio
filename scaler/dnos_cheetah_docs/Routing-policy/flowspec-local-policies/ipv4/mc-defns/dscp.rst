routing-policy flowspec-local-policies ipv4 match-class dscp
------------------------------------------------------------

**Minimum user role:** operator

Configures the dscp as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: dscp [dscp]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Parameter table**

+-----------+-------------------------------------+-------+---------+
| Parameter | Description                         | Range | Default |
+===========+=====================================+=======+=========+
| dscp      | Differentiated Services Code Point. | 0-63  | \-      |
+-----------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# dscp 45
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove the dscp from the match class:
::

    dnRouter(cfg-flp-ipv4-mc)# no dscp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
