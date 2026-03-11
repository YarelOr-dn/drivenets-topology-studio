protocols segment-routing mpls path dynamic constraints admin-group exclude
---------------------------------------------------------------------------

**Minimum user role:** operator

A link is not valid for to be used in dynamic path if the link has any admin-group value that matches the admin-group-exclude values.
To configure a admin-group exclude constraint:

**Command syntax: admin-group exclude [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from dynamic-path if link has any admin-group value that match the  | | string         | \-      |
|                  | admin-group-exclude values                                                       | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# dynamic
    dnRouter(cfg-mpls-path-dynamic)# constraints
    dnRouter(cfg-path-dynamic-constraints)# admin-group exclude RED,GREEN


**Removing Configuration**

To remove a specific admin-group exclude configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group exclude RED

To remove all admin-group exclude configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group exclude

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
