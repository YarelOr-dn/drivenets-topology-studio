qos hw-mapping queue-size speed-ranges upto
-------------------------------------------

**Minimum user role:** operator

Ranges are specified by the upper speed limit and the speed value to be used for the conversion. The ranges are ordered by their upper limit in ascending order. The lower range limit is implicitly defined by the upper limit of the predecessing range.

To configure a speed range for unit conversion:

**Command syntax: upto [ranges] [units1] use [use] [units2]**

**Command mode:** config

**Hierarchies**

- qos hw-mapping queue-size speed-ranges

**Parameter table**

+-----------+-----------------------------------------------------+-----------------+---------+
| Parameter | Description                                         | Range           | Default |
+===========+=====================================================+=================+=========+
| ranges    | References the configured lower limit of the range. | 1-1000000000000 | \-      |
+-----------+-----------------------------------------------------+-----------------+---------+
| units1    |                                                     | | kbps          | kbps    |
|           |                                                     | | mbps          |         |
|           |                                                     | | gbps          |         |
+-----------+-----------------------------------------------------+-----------------+---------+
| use       | speed used for unit conversion.                     | 1-1000000000000 | \-      |
+-----------+-----------------------------------------------------+-----------------+---------+
| units2    |                                                     | | kbps          | kbps    |
|           |                                                     | | mbps          |         |
|           |                                                     | | gbps          |         |
+-----------+-----------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)# queue-size
    dnRouter(cfg-qos-hw-map-queue)# speed-ranges
    dnRouter(cfg-hw-map-queue-speed-ranges)# upto 200 gbps use 100 gbps


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-hw-map-queue-speed-ranges)# no upto 200 gbps use 100 gbps

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
