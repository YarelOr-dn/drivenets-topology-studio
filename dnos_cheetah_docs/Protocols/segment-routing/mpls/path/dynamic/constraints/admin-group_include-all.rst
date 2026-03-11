protocols segment-routing mpls path dynamic constraints admin-group include-all
-------------------------------------------------------------------------------

**Minimum user role:** operator

A link is not valid for to be used in dynamic path if the link doesn't match all admin-group values that are in the admin-group-include-all values.
To configure a admin-group include-all constraint:

**Command syntax: admin-group include-all [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path dynamic constraints

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from dynamic-path if link don't match all admin-group values that   | | string         | \-      |
|                  | are in the admin-group-include-all values                                        | | length 1-255   |         |
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
    dnRouter(cfg-path-dynamic-constraints)# admin-group include-all RED,GREEN


**Removing Configuration**

To remove a specific admin-group include-all configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group include-all RED

To remove all admin-group include-all configuration:
::

    dnRouter(cfg-path-dynamic-constraints)# no admin-group include-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
