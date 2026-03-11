nacm group
----------

**Minimum user role:** admin

One NACM group entry. This list will only contain configured entries, not any entries learned from any transport protocols.

**Command syntax: group [group]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+-----------+----------------------------------------+-------+---------+
| Parameter | Description                            | Range | Default |
+===========+========================================+=======+=========+
| group     | Group name associated with this entry. | \-    | \-      |
+-----------+----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# group group1
    dnRouter(cfg-nacm-group-group1)#


**Removing Configuration**

To delete group:
::

    dnRouter(cfg-nacm)# no group group1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
