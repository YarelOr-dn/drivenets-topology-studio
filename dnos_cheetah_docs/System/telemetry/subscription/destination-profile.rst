system telemetry subscription destination-profile
-------------------------------------------------

**Minimum user role:** operator

The Destination Profile is the attachment of a Destination Group to a subscription:

**Command syntax: destination-profile [destination-profile]**

**Command mode:** config

**Hierarchies**

- system telemetry subscription

**Parameter table**

+---------------------+-----------------------------------------------+------------------+---------+
| Parameter           | Description                                   | Range            | Default |
+=====================+===============================================+==================+=========+
| destination-profile | Destination Group to link to the Subscription | | string         | \-      |
|                     |                                               | | length 1-255   |         |
+---------------------+-----------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# subscription my-subscription
    dnRouter(cfg-system-telemetry-subscription)# destination-profile DGroup
    dnRouter(cfg-system-telemetry-subscription)#


**Removing Configuration**

To remove a specific destination-profile from the subscription:
::

    dnRouter(cfg-system-telemetry-subscription)# no destination-profile DGroup

To remove all clients from the client-list:
::

    dnRouter(cfg-system-telemetry-subscription)# no destination-profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
