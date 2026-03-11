show qos summary
----------------

**Minimum user role:** viewer

This command displays a concentric view of the QoS information per interface.

To display the QoS summary table:

**Command syntax: show qos summary**

**Command mode:** operational

.. **Note**

	- Bundle interfaces prints out the total packets matched and dropped on all bundle interface members. Bundle memberes are not shown here.

**Parameter table**

+-------------+--------------------------------------------------------------------------------------------+
| Parameter   | Description                                                                                |
+=============+============================================================================================+
| Interface   | The name of the interface to which a QoS policy is attached                                |
+-------------+--------------------------------------------------------------------------------------------+
| Direction   | The direction in which the policy is attached (in - ingress traffic; out - egress traffic) |
+-------------+--------------------------------------------------------------------------------------------+
| Policy      | The name of the policy that is attached to the interface                                   |
+-------------+--------------------------------------------------------------------------------------------+
| Rule        | The rule ID                                                                                |
+-------------+--------------------------------------------------------------------------------------------+
| Match       | The total number of packets/Mbps that matched the rule                                     |
+-------------+--------------------------------------------------------------------------------------------+
| Total Drops | The total number of packets/Mbps that were dropped per rule                                |
+-------------+--------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show qos summary

	r (remaining) : untagged traffic and traffic not captured by sub-interface policies

	| Interface         | Direction  | Policy     | Rule    | Traffic-class | Match[Mbps] | Drop[Mbps]  | Transmit[Mbps]| Match[pkts] | Drop[pkts]  | Transmit[pkts]|
	|-------------------+------------+------------+---------+---------------+-------------+-------------|---------------|-------------+-------------|---------------|
	| ge100-2/0/1 (r)   | in         | ingress-p  | default |               | 0           | 0           | 0             | 100         | 3           | 97            |
	| ge100-2/0/1 (r)   | out        | egress-p   | default |               | 0           | 0           | 0             | 58          | 0           | 58            |
	| ge100-2/0/1.100   | in         | ingress-p  | default |               | 0           | 0           | 0             | 5900        | 0           | 5900          |
	| ge100-2/0/1.100   | out        | egress-p   | default |               | 0           | 0           | 0             | 23400       | 0           | 23400         |
	| ge100-2/0/1.200   | in         | ingress-p  | default |               | 0           | 0           | 0             | 4000        | 0           | 4000          |
	| ge100-2/0/1.200   | out        | egress-p   | default |               | 0           | 0           | 0             | 100000      | 0           | 100000        |
	| ge100-5/0/1.300   | in         | ingress-p  | default |               | 0           | 0           | 0             | 5900        | 0           | 5900          |
	| ge100-5/0/1.300   | out        | egress-p   | default |               | 0           | 0           | 0             | 23400       | 0           | 23400         |
	| ge100-5/0/1.400   | in         | ingress-p  | default |               | 0           | 0           | 0             | 4000        | 0           | 4000          |
	| ge100-5/0/1.400   | out        | egress-p   | default |               | 0           | 0           | 0             | 100000      | 0           | 100000        |
	| ge100-12/0/1      | in         | ingress-p  | default |               | 0           | 0           | 0             | 100         | 3           | 97            |
	| ge100-12/0/1      | out        | egress-p   | default |               | 0           | 0           | 0             | 100000      | 0           | 100000        |
	| bundle-3          | in         | ingress-p  | 1       | Class4        | 2.3         | 1.2         | 1.1           | 8654321     | 4334333     | 4319988       |
	| bundle-3          | in         | ingress-p  | default |               | 0           | 0           | 0             | 734321      | 0           | 734321        |
	| bundle-3          | out        | egress-p   | 1       | RealTime      | 170.3       | 44.3        | 126           | 7654321     | 4444        | 7649877       |
	| bundle-3          | out        | egress-p   | default |               | 50.4        | 23.33       | 27.04         | 8721        | 23          | 8698          |

.. **Help line:** show summary of all policies attached to interfaces including counters

**Command History**

+---------+------------------------------+
| Release | Modification                 |
+=========+==============================+
| 11.2    | Command introduced           |
+---------+------------------------------+
| 11.4    | Added Match and Drop in Mbps |
+---------+------------------------------+
