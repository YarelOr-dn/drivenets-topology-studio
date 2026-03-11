services ipsec terminator src-mac
---------------------------------

**Minimum user role:** operator

src-mac the ipsec-terminator will use.

**Command syntax: src-mac [src-mac]**

**Command mode:** config

**Hierarchies**

- services ipsec terminator

**Parameter table**

+-----------+----------------------------------------+-------+---------+
| Parameter | Description                            | Range | Default |
+===========+========================================+=======+=========+
| src-mac   | src-mac the ipsec-terminator will use. | \-    | \-      |
+-----------+----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# terminator 1 src-mac AA:BB:CC:DD:EE:FF


**Removing Configuration**

To revert the admis-state to the default value:
::

    dnRouter(cfg-srv-ipsec)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
