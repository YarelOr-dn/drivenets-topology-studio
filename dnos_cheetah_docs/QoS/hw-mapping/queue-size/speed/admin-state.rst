qos hw-mapping queue-size speed-ranges admin-state
--------------------------------------------------

**Minimum user role:** operator

To enable/disable speed range conversion table:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- qos hw-mapping queue-size speed-ranges

**Parameter table**

+-------------+----------------------------------------------+--------------+---------+
| Parameter   | Description                                  | Range        | Default |
+=============+==============================================+==============+=========+
| admin-state | Set to enable to use the speed range tables. | | enabled    | enabled |
|             |                                              | | disabled   |         |
+-------------+----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)# queue-size
    dnRouter(cfg-qos-hw-map-queue)# speed-ranges
    dnRouter(cfg-hw-map-queue-speed-ranges)# admin-state enabled


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-hw-map-queue-speed-ranges)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
