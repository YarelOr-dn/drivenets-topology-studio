protocols ospf instance maximum-ecmp-paths
------------------------------------------

**Minimum user role:** operator

To configure the OSPF maximum ECMP path limit:

**Command syntax: maximum-ecmp-paths [maximum-ecmp-paths]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

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
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# maximum-ecmp-paths 20


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospf)# no maximum-ecmp-paths

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
