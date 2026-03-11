protocols ospfv3 maximum-ecmp-paths
-----------------------------------

**Minimum user role:** operator

To configure the OSPFV3 maximum ECMP path limit:

**Command syntax: maximum-ecmp-paths [maximum-ecmp-paths]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- On-startup and On-shutdown may be configured simultaneously and are mutually exclusive with "administrative".

**Parameter table**

+--------------------+-------------------------------------------+-------+---------+
| Parameter          | Description                               | Range | Default |
+====================+===========================================+=======+=========+
| maximum-ecmp-paths | Maximum ECMP paths that OSPF can support. | 1-32  | 32      |
+--------------------+-------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-ecmp-paths 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-ecmp-paths

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 11.6    | Command introduced        |
+---------+---------------------------+
| 13.1    | Added support for OSPFv3  |
+---------+---------------------------+
