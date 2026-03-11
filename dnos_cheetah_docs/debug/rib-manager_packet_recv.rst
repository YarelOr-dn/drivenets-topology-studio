debug rib-manager packet recv
-----------------------------

**Minimum user role:** operator

To debug RIB manager packet:

**Command syntax: rib-manager packet recv** detail

**Command mode:** config

**Hierarchies**

- debug

**Note**
- You can set either packet receive, packet recv, or packet only for both receive and recv.

**Parameter table**

+-----------+-------------------------------+---------+---------+
| Parameter | Description                   | Range   | Default |
+===========+===============================+=========+=========+
| detail    | enable detailed debug logging | Boolean | False   |
+-----------+-------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# debug
    dnRouter(cfg-debug)# rib-manager packet recv
    dnRouter(cfg-debug)# rib-manager packet recv detail


**Removing Configuration**

To remove debug configuration:
::

    dnRouter(cfg-debug)# no rib-manager packet recv

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 6.0     | Command introduced          |
+---------+-----------------------------+
| 11.5    | Applied new debug hierarchy |
+---------+-----------------------------+
