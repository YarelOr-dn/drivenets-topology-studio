qos hw-mapping queue-size speed-ranges
--------------------------------------

**Minimum user role:** operator

Queue sizes are specified in temporal units (e.g. msec) are mapped to absolute units depending on the maximum queue depletion rate, determined by the interface speed or the queue shaper maximum rate. To maintain a small set of possible queue and thresholds sizes, the queue depletion rate is compared against a set of speed ranges, and the matching speed range determines the speed that is used for the conversion.

To configure the speed ranges used for temporal to absolute unit conversion:

**Command syntax: speed-ranges**

**Command mode:** config

**Hierarchies**

- qos hw-mapping queue-size

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)# queue-size
    dnRouter(cfg-qos-hw-map-queue)# speed-ranges
    dnRouter(cfg-hw-map-queue-speed-ranges)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qos-hw-map-queue)# no speed-ranges

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
