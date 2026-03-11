tracking-policy ignore-default-route
------------------------------------

**Minimum user role:** operator

Configure whether, if the default-route is being tracked, and if it should be ignored during validation.

**Command syntax: ignore-default-route [ignore-default-route]**

**Command mode:** config

**Hierarchies**

- tracking-policy

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter            | Description                                                                      | Range        | Default  |
+======================+==================================================================================+==============+==========+
| ignore-default-route | Configure whether to ignore the default route, when validating if the subnet on  | | enabled    | disabled |
|                      | an AC is within the subnet of the route it is tracking                           | | disabled   |          |
+----------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# ignore-default-route enabled
    dnRouter(cfg-trkpl)#


**Removing Configuration**

To restore the ignore-default-route field to its default value.
::

    dnRouter(cfg-trkpl)# no ignore-default-route

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
