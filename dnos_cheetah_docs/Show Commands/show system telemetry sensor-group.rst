show system telemetry sensor-group
----------------------------------

**Minimum user role:** viewer

The sensor path state can be either be resolved or not resolved. The resolved status indicates that the sensor path has been verified against the devices existing YANG model. An unresolved status indicates that the sensor path is not verified against the device existing YANG model. If the path is not resolved, the sensor path error field contains the reason for the failure. To display information on dial-out telemetry sensor group paths, resolved status, and use in subscriptions:

**Command syntax: show system telemetry sensor-group** [sensor-group-id]

**Command mode:** operational

**Parameter table**

+-----------------+---------------------------------------+---------+
| Parameter       | Description                           | Default |
+=================+=======================================+=========+
| sensor-group-id | Optionally filter the information for | \-      |
|                 | a specific sensor group               |         |
|                 |                                       |         |
+-----------------+---------------------------------------+---------+

.. **Note**

**Example**
::

    dnRouter# show system telemetry sensor-group

    Sensor Group Id: bundle-octets-counters
    ---------------------------------------

    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/rx-octets
    Sensor Path State:  Resolved
    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/tx-octets
    Sensor Path State:  Resolved
    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/dummy-container/tx-octets
    Sensor Path State:  Not Resolved
    Sensor Path Error:  Path could not be resolved

    Used by subscriptions:
      dev-subscription  sample interval 10 seconds
      prod-subscription sample interval 20 seconds

    Sensor Group Id: ge100-0/0/3-physicals-counters
    -----------------------------------------------

    Sensor Path:        /drivenets-top/interfaces/interface[name='ge100-0/0/3']/oper-items/counters/ethernet-counters
    Sensor Path State:  Resolved

    Used by subscriptions:
        none

    dnRouter# show system telemetry sensor-group bundle-octets-counters

    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/rx-octets
    Sensor Path State:  Resolved
    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/forwarding-counters/tx-octets
    Sensor Path State:  Resolved
    Sensor Path:        /drivenets-top/interfaces/interface[name='bundle*']/oper-items/counters/dummy-container/tx-octets
    Sensor Path State:  Not Resolved
    Sensor Path Error:  Path could not be resolved

    Used by subscriptions:
      dev-subscription  sample interval 10 seconds
      prod-subscription sample interval 20 seconds



.. **Help line:** show system telemetry sensor-group

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.10   | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
