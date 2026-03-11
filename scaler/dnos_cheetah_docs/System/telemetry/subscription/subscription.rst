system telemetry subscription
-----------------------------

**Minimum user role:** operator

To configure a dial-out telemetry subscription:

**Command syntax: subscription [subscription]**

**Command mode:** config

**Hierarchies**

- system telemetry

**Note**

- Up to 16 subscriptions can be configured.

**Parameter table**

+--------------+-----------------------------------------+------------------+---------+
| Parameter    | Description                             | Range            | Default |
+==============+=========================================+==================+=========+
| subscription | Unique identifier for the subscription. | | string         | \-      |
|              |                                         | | length 1-255   |         |
+--------------+-----------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# subscription my-subscription
    dnRouter(cfg-system-telemetry-subscription)#


**Removing Configuration**

To delete the configuration under subscription:
::

    dnRouter(cfg-system-telemetry)# no subscription my-subscription

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
