qos ecn-profile min-threshold
-----------------------------

**Minimum user role:** operator

To configure the ECN profile min-threshold which is the lower value for the range of the curve, below which no packets will be marked:

**Command syntax: min-threshold [min-threshold-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos ecn-profile

**Note**

- The ECN profile must be configured with a min-threshold and a max-threshold.

- The min-value must be less or equal to the max-value.

**Parameter table**

+----------------------------+-----------------------------------------------+------------------+--------------+
| Parameter                  | Description                                   | Range            | Default      |
+============================+===============================================+==================+==============+
| min-threshold-microseconds | Queue minimum drop threshold in microseconds. | 1-200000         | \-           |
+----------------------------+-----------------------------------------------+------------------+--------------+
| units                      |                                               | | microseconds   | microseconds |
|                            |                                               | | milliseconds   |              |
+----------------------------+-----------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1
    dnRouter(cfg-qos-MyEcnProfile1)# min-threshold 10000 microseconds


**Removing Configuration**

To remove the min threshold:
::

    dnRouter(cfg-qos-MyEcnProfile1)# no min-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
