protocols bgp label-retention
-----------------------------

**Minimum user role:** operator

There are cases where BGP is required to the change the locally allocated labels for the same prefix:

-	For a label per prefix - when the best-path to a prefix has changed from being second-best (bgp-external) to first-best.

-	For a label per nexthop - when the nexthop has changed.

In both cases, to allow for a smooth label transition in the network, bgp will install a new label and retain the previous label installed in FIB for a defined period. This period is the BGP label retention timer.

To configure the label-retention timer:

**Command syntax: label-retention [label-retention-time]**

**Command mode:** config

**Hierarchies**

- protocols bgp

**Parameter table**

+----------------------+-------------+-------+---------+
| Parameter            | Description | Range | Default |
+======================+=============+=======+=========+
| label-retention-time | Munites     | 3-60  | 5       |
+----------------------+-------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# label-retention 10


**Removing Configuration**

To revert BGP label-retention parameter to its default value:
::

    dnRouter(cfg-protocols-bgp)# no label-retention

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
