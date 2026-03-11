protocols ospf instance ti-fast-reroute maximum-labels
------------------------------------------------------

**Minimum user role:** operator

Sets the maximum allowed number of labels on the TI-LFA constructed label stack.
If the calculated path exceeds the allowed maximum, an LFA path will not be provided by OSPF and no alternate path will be installed.
To set the maximum-labels:

**Command syntax: maximum-labels [maximum-labels]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance ti-fast-reroute

**Parameter table**

+----------------+------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                            | Range | Default |
+================+========================================================================+=======+=========+
| maximum-labels | Set the maximum number of allowed additional labels in the SR LFA path | 1-5   | 3       |
+----------------+------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# ti-fast-reroute
    dnRouter(cfg-protocols-ospf-ti-frr)# maximum-labels 2


**Removing Configuration**

To revert maximum-labels to the default value:
::

    dnRouter(cfg-protocols-ospf-ti-frr)# no maximum-labels

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
