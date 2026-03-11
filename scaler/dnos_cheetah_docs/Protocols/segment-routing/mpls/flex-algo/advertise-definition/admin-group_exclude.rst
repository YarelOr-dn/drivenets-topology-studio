protocols segment-routing mpls flex-algo advertise-definition admin-group exclude
---------------------------------------------------------------------------------

**Minimum user role:** operator

A link is pruned from the Flex-Algo topology if the link has any admin-group value that matches the admin-group-exclude values.
To configure an admin-group exclude constraint:

**Command syntax: admin-group exclude [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from flex-algo topology if link has any admin-group value that      | | string         | \-      |
|                  | match the admin-group-exclude values                                             | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# admin-group exclude RED,GREEN


**Removing Configuration**

To remove a specific admin-group exclude configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group exclude RED

To remove all admin-group exclude configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group exclude

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
