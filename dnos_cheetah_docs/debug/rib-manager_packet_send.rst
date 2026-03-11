debug rib-manager packet send
-----------------------------

**Minimum user role:** operator

To debug RIB manager packet:

**Command syntax: rib-manager packet send** detail

**Command mode:** config

**Hierarchies**

- debug

**Note**
- You can set either packet receive, packet send, or packet only for both receive and send.

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
    dnRouter(cfg-debug)# rib-manager packet send
    dnRouter(cfg-debug)# rib-manager packet send detail


**Removing Configuration**

To remove debug configuration:
::

    dnRouter(cfg-debug)# no rib-manager packet send

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 6.0     | Command introduced          |
+---------+-----------------------------+
| 11.5    | Applied new debug hierarchy |
+---------+-----------------------------+
