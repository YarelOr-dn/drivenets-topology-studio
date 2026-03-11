protocols segment-routing mpls flex-algo advertise-definition admin-group include-all
-------------------------------------------------------------------------------------

**Minimum user role:** operator

A link is pruned from the Flex-Algo topology if the link doesn't match all admin-group values that are in the admin-group-include-all values.
To configure an admin-group include-all constraint:

**Command syntax: admin-group include-all [admin-group name]** [, admin-group name, admin-group name]

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls flex-algo advertise-definition

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| admin-group name | link is prun from flex-algo topology if link don't match all admin-group values  | | string         | \-      |
|                  | that are in the admin-group-include-all values                                   | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# flex-algo
    dnRouter(cfg-sr-mpls-flex-algo)# advertise-definition MIN_DELAY_130
    dnRouter(cfg-mpls-flex-algo-fad)# admin-group include-all RED,GREEN


**Removing Configuration**

To remove a specific admin-group include-all configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group include-all RED

To remove all admin-group include-all configuration:
::

    dnRouter(cfg-mpls-flex-algo-fad)# no admin-group include-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
