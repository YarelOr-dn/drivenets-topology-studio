qos ecn-profile
---------------

**Minimum user role:** operator

The purpose of the Explicit Congestion Notification (ECN) is to mark packets going through a congested path.
When used, ECN signals the sender to slow the transmittion rate.
The packet marking probability is based on a minimum threshold, a maximum threshold and a linear curve that starts at a 0 drop probability and ends at max-drop-probability.
To allow small bursts with no marking, the minimum and maximum thresholds relate to the average queue size and not to the current queue size.

**Command syntax: ecn-profile [ecn-profile]**

**Command mode:** config

**Hierarchies**

- qos

**Note**

- You cannot remove a profile if it is part of qos policy that is attached to an interface.

**Parameter table**

+-------------+-----------------------------------------------+------------------+---------+
| Parameter   | Description                                   | Range            | Default |
+=============+===============================================+==================+=========+
| ecn-profile | References the configured name of the profile | | string         | \-      |
|             |                                               | | length 1-255   |         |
+-------------+-----------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# ecn-profile MyEcnProfile1


**Removing Configuration**

To remove the ECN profile:
::

    dnRouter(cfg-qos)# no ecn-profile MyEcnProfile1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
