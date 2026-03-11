clear telemetry counters
------------------------

**Minimum user role:** operator

To clear telemetry dial-out counters for each specific destination and/or destination-profile and/or subscription and/or system:

**Command syntax: clear grpc counters** [subscription <subscription-id>] [destination-profile <destination-profile-id>] [ip <ip>] [port <port>]

**Command mode:** operation

.. **Hierarchies**

**Note**

- A command without a specific parameter clears the counters for all subscriptions and destinations in the system.


**Parameter table:**

+------------------------+--------------------------------------------+--------------------+
| Parameter              |        Description                         |   Range            |
+========================+============================================+====================+
| subscription-id        | The ID of the specific subscription        | 1..255 characters  |
+------------------------+--------------------------------------------+--------------------+
| destination-profile-id | The ID of the specific destination-profile | 1..255 characters  |
+------------------------+--------------------------------------------+--------------------+
| ip                     | The IP address of destination              | A.B.C.D            |
|                        |                                            | xx:xx::xx:xx       |
+------------------------+--------------------------------------------+--------------------+
| port                   | The destination port                       | 0..65535           |
+------------------------+--------------------------------------------+--------------------+

**Example**
::

	dnRouter# clear telemetry counters
	dnRouter# clear telemetry counters subscription-id dev-subscription
	dnRouter# clear telemetry counters subscription-id dev-subscription destination-profile Development
	dnRouter# clear telemetry counters destination-profile Development
	dnRouter# clear telemetry counters subscription-id dev-subscription destination-profile Development destination-ip 10.0.0.1 destination-port 62000



**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 19.10       | Command introduced    |
+-------------+-----------------------+
