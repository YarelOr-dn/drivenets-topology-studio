system telemetry subscription sensor-profile
--------------------------------------------

**Minimum user role:** operator

Sensor Profile is the attachment of a Sensor Group to a subscription:

**Command syntax: sensor-profile [sensor-profile]**

**Command mode:** config

**Hierarchies**

- system telemetry subscription

**Note**

- Up to 16 sensor profiles can be configured in subscription.

**Parameter table**

+----------------+--------------------------------------------------+------------------+---------+
| Parameter      | Description                                      | Range            | Default |
+================+==================================================+==================+=========+
| sensor-profile | The Sensor Group that links to the subscription. | | string         | \-      |
|                |                                                  | | length 1-255   |         |
+----------------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# subscription my-subscription
    dnRouter(cfg-system-telemetry-subscription)# sensor-profile bundle-collection
    dnRouter(cfg-telemetry-subscription-snsrprof)#


**Removing Configuration**

To delete the configuration under sensor profile:
::

    dnRouter(cfg-system-telemetry)# no sensor-profile bundle-collection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
