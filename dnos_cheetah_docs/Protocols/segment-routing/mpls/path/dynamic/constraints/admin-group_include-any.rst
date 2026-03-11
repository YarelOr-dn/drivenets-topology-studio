protocols segment-routing mpls path dynamic constraints admin-group include-any
-------------------------------------------------------------------------------

**Minimum user role:** operator

A link is not valid for to be used in dynamic path if the link doesn't match any admin-group values that are in the admin-group-include-any values.
To configure a admin-group include-any constraint:

**Command syntax: admin-group include-any [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from dynamic-path if link don't match any admin-group value that is | | string         | \-      |
|                  | in the admin-group-include-any values                                            | | length 1-255   |         |
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
    dnRouter(cfg-path-dynamic-constraints)# admin-group include-any RED,GREEN


**Removing Configuration**

To remove a specific admin-group include-any configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group include-any RED

To remove all admin-group include-any configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group include-any

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
