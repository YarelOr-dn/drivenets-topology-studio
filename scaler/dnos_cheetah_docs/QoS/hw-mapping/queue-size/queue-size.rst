qos hw-mapping queue-size
-------------------------

**Minimum user role:** operator

To configure rules for mapping queue-size related policies to hardware settings.


**Command syntax: queue-size**

**Command mode:** config

**Hierarchies**

- qos hw-mapping

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)# queue-size
    dnRouter(cfg-qos-hw-map-queue)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qos-hw-map)# no queue-size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
