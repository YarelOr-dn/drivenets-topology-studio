protocols ospf instance microloop-avoidance maximum-labels
----------------------------------------------------------

**Minimum user role:** operator

Sets the maximum allowed number of labels on the SR-TE microloop-avoidance constructed label stack.
If the calculated path exceeds the allowed maximum, than a microloop-avoidance path will not be provided by OSPF.
To set the maximum-labels:

**Command syntax: maximum-labels [maximum-labels]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance microloop-avoidance

**Note**

- The microloop avoidance maximum-labels parameter is per OSPF topology.

**Parameter table**

+----------------+-----------------------------------------------------------+-------+---------+
| Parameter      | Description                                               | Range | Default |
+================+===========================================================+=======+=========+
| maximum-labels | Maximum allowed labels to be added for the microloop path | 1-3   | 3       |
+----------------+-----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# microloop-avoidance
    dnRouter(cfg-ospf-inst-uloop)# maximum-labels 1


**Removing Configuration**

To revert maximum-labels to the default value:
::

    dnRouter(cfg-inst-afi-uloop)# no maximum-labels

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
