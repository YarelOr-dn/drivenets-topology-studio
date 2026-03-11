qos wred-profile
-----------------

**Minimum user role:** operator

The purpose of the Weighted Random Early Detection (WRED) profile is to avoid congestion on the queue by starting to drop packets randomly before the queue reaches its maximum limit. By dropping packets randomly, WRED signals to the sender to slow down the transmission rate (the mechanism accompanies a transport-layer congestion control protocol such as TCP).

The packet drop probability is based on a minimum threshold, a maximum threshold and a linear curve that starts at 0 drop probability and crosses the maximum drop probability threshold at 10%. You can set up to two curves (yellow/green) for AF/DF forwarding classes and up to a total of 16 WRED profiles. 

When configuring the curves for each forwarding class, you should take into account the queue's size (see "qos policy rule action queue size"). You can then decide when each curve should start dropping packets. You should set the minimum threshold high enough to maximize the utilization of the queue capacity. The minimum threshold should not be higher than the queue size configured for the forwarding class.

When the average queue size crosses the min-threshold, WRED begins to drop packets randomly. The drop probability increases until the average queue size reaches the maximum threshold. When the average queue size exceeds the maximum threshold, all packets are dropped.


.. The average queue size is calculated as follows:

To configure a WRED profile:

#.	Enter WRED profile configuration hierarchy (see below)
#.	Configure a curve.

**Command syntax: wred-profile [profile-name] curve [green|yellow] min [min-value] [min-knob] max [max-value] [max-knob]** max-drop [max-drop]

**Command mode:** config

**Hierarchies**

- qos 

**Note**

- The average queue size refers to the (ingress) virtual output queue (VOQ). 

- To allow small bursts with no drops, the min- and max-values relate to the average queue size and not to the current queue size.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| Parameter       | Description                                                                                                                                                                                                                    | Range                     | Default     |
+=================+================================================================================================================================================================================================================================+===========================+=============+
|                 |                                                                                                                                                                                                                                |                           |             |
| profile-name    | The name of the profile. If the profile name   already exists, the command will update the values of the parameters. If the   profile name does not exist, a new profile is created with the configured   parameter values.    | String                    |  \-         |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| min-value       | Specify the lower value for the range of the   curve, below which no packets will be dropped.                                                                                                                                  | 1..2000000 (microseconds) | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 | The min-value must be less or equal to the   max-value                                                                                                                                                                         | 1..200 (milliseconds)     |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| min-knob        | Set the unit of measurement for the min value                                                                                                                                                                                  | microseconds              | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 |                                                                                                                                                                                                                                | milliseconds              |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-value       | Specify the upper value for the range of the curve,   above which all packets will be dropped.                                                                                                                                 | 1..2000000 (microseconds) | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 | The max-value must be equal or greater than   min-value.                                                                                                                                                                       | 1..200 (milliseconds)     |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-knob        | Set the unit of measurement for the max value                                                                                                                                                                                  | microseconds              | \-          |
|                 |                                                                                                                                                                                                                                |                           |             |
|                 |                                                                                                                                                                                                                                | milliseconds              |             |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+
|                 |                                                                                                                                                                                                                                |                           |             |
| max-drop        | The maximum drop probability per curve                                                                                                                                                                                         | 1..100%                   | 10%         |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# wred-profile my_profile
	dnRouter(cfg-qos-wred-profile-my_profile)# curve green min 500 milliseconds max 1000 milliseconds
	dnRouter(cfg-qos-wred-profile-my_profile)# curve yellow min 100 milliseconds max 800 milliseconds

	dnRouter(cfg-qos)# wred-profile my_profile2
	dnRouter(cfg-qos-wred-profile-my_profile2)# curve green min 10 milliseconds max 100 milliseconds


**Removing Configuration**

You cannot delete a WRED profile if it is attached to a queue. You must first delete the profile from the queue. See "qos policy rule action queue wred-profile".

To remove the WRED profile configuration:
::

	dnRouter(cfg-qos)# no wred-profile
	dnRouter(cfg-qos)# no wred-profile my_profile


To remove a curve from the profile:
::

	dnRouter(cfg-qos-wred-profile-default)# no curve green


.. **Help line:** Configure wred curves per drop priority

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
|             |                                         |
| 5.1.0       | Command introduced                      |
+-------------+-----------------------------------------+
|             |                                         |
| 6.0         | Applied   new hierarchy                 |
+-------------+-----------------------------------------+
|             |                                         |
| 9.0         | Command not supported                   |
+-------------+-----------------------------------------+
|             |                                         |
| 11.4        | Command reintroduced with new syntax    |
+-------------+-----------------------------------------+
|             |                                         |
| 15.1        | Added support for max-drop              |
+-------------+-----------------------------------------+
|             |                                         |
| 18.3        | Added min-threshold knob                |
+-------------+-----------------------------------------+