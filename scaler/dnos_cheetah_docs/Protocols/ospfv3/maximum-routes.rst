protocols ospfv3 maximum-routes
-------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum routes and threshold limit.

**Command syntax: maximum-routes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'no maximum-routes' returns the maximum and threshold to their default values.

**Parameter table**

+-----------+------------------------------------------------------+--------------+---------+
| Parameter | Description                                          | Range        | Default |
+===========+======================================================+==============+=========+
| maximum   | maximum number of routes.                            | 1-4294967295 | 32000   |
+-----------+------------------------------------------------------+--------------+---------+
| threshold | threshold as a percentage of maximum allowed routes. | 1-100        | 75      |
+-----------+------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# maximum-routes 90000
    dnRouter(cfg-protocols-ospfv3)# maximum-routes 90000 threshold 80


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospfv3)# no maximum-routes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
