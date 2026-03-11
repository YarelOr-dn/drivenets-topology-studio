system telemetry subscription sensor-profile sample-interval
------------------------------------------------------------

**Minimum user role:** operator

To configure a sample-interval for a sensor-profile, which is the interval between two consecutive samples for the sensor-profile:

**Command syntax: sample-interval [sample-interval]**

**Command mode:** config

**Hierarchies**

- system telemetry subscription sensor-profile

**Parameter table**

+-----------------+-----------------------------+---------+---------+
| Parameter       | Description                 | Range   | Default |
+=================+=============================+=========+=========+
| sample-interval | Sample interval in seconds. | 5-86400 | \-      |
+-----------------+-----------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# subscription my-subscription
    dnRouter(cfg-system-telemetry-subscription)# sensor-profile bundle-collection
    dnRouter(cfg-telemetry-subscription-snsrprof)# sample-interval 30


**Removing Configuration**

To remove sample-interval from sensor profile:
::

    dnRouter(cfg-telemetry-subscription-snsrprof)# no sample-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
