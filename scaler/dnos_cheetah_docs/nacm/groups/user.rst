nacm group user-name
--------------------

**Minimum user role:** admin

Each entry identifies the username of a member of the group associated with this entry.

**Command syntax: user-name [user-name]** [, user-name, user-name]

**Command mode:** config

**Hierarchies**

- nacm group

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| user-name | Each entry identifies the username of a member of the group associated with this | \-    | \-      |
|           | entry.                                                                           |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# group group1
    dnRouter(cfg-nacm-group-group1)# user-name user1


**Removing Configuration**

To delete user-name:
::

    dnRouter(cfg-nacm-group-group1)# no user-name user1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
