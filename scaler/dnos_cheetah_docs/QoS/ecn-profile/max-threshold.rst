qos ecn-profile max-threshold
-----------------------------

**Minimum user role:** operator

To configure the ECN profile max-threshold which is the upper value for the range of the curve, above which all packets will be marked:

**Command syntax: max-threshold [max-threshold-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Note**

- The ECN profile must be configured with both a min-threshold and max-threshold.

- The min-value must be less or equal to the max-value.

**Parameter table**

+----------------------------+-----------------------------------------------+------------------+--------------+
| Parameter                  | Description                                   | Range            | Default      |
+============================+===============================================+==================+==============+
| max-threshold-microseconds | Queue maximum drop threshold in microseconds. | 1-200000         | \-           |
+----------------------------+-----------------------------------------------+------------------+--------------+
| units                      |                                               | | microseconds   | microseconds |
|                            |                                               | | milliseconds   |              |
+----------------------------+-----------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# max-threshold 10000 microseconds


**Removing Configuration**

To remove the max threshold:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no max-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
