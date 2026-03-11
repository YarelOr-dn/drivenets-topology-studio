protocols segment-routing mpls flex-algo advertise-definition admin-group include-any
-------------------------------------------------------------------------------------

**Minimum user role:** operator

A link is pruned from the Flex-Algo topology if the link doesn't match any admin-group values that are in the admin-group-include-any values.
To configure an admin-group include-any constraint:

**Command syntax: admin-group include-any [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from flex-algo topology if link don't match any admin-group value   | | string         | \-      |
|                  | that is in the admin-group-include-any values                                    | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# admin-group include-any RED,GREEN


**Removing Configuration**

To remove a specific admin-group include-any configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group include-any RED

To remove all admin-group include-any configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group include-any

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
