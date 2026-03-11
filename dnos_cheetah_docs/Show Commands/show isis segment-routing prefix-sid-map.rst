show isis segment-routing prefix-sid-map
----------------------------------------

**Minimum user role:** viewer

To display the received prefix-sid-map mapping when acting as a mapping client:



**Command syntax: show show isis** instance [isis-instance-name] **segment-routing prefix-sid-map** backup

**Command mode:** operational




**Parameter table**

+--------------------+----------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                              |
+====================+==========================================================================================================+
| isis-instance-name | Filters the displayed information to the specified instance.                                             |
+--------------------+----------------------------------------------------------------------------------------------------------+
| backup             | Displays the backup mapping, containing the least preferred FECs according to SRMS conflicts resolution. |
+--------------------+----------------------------------------------------------------------------------------------------------+

The following information is displayed per prefix:

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter         | Description                                                                                                                                                   |
+===================+===============================================================================================================================================================+
| prefix            | The prefix for which a SID was assigned                                                                                                                       |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| SID value         | The prefix SID absolute value from the local SRGB                                                                                                             |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| SID Index         | The prefix SID index from the local SRGB                                                                                                                      |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Range             | The prefix range that is advertised by the SRMS                                                                                                               |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Last Prefix       | The last prefix that was mapped. The binding mapping is received with an initial prefix and a range; together they form the list of prefixes that are mapped. |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| P-Flags           | The state if any of the Prefix-SID R, N, P, E, V or L flags are set                                                                                           |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| B-Flags           | The state if any of the Binding-SID F, M, S, D or A flags are set                                                                                             |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Advertised System | The IS-IS hostname (or system ID if the hostname does not exist) of the router that advertised the mapping.                                                   |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Mapping server    | The system-ID (or host name if known) of the SRMS from which the mapping was received                                                                         |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Preferences       | The mapping server preference. If not received from mapping server, a value of 128 is assumed                                                                 |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis segment-routing prefix-sid-map

	Instance INSTANCE_1
	Level 1:
	Active Binding-SIDs:
	| Prefix     | SID index | Range | Last Prefix | P-Flags | B-Flags | Advertised System | Preference |
	+------------+-----------+-------+-------------+---------+---------+-------------------+------------+
	| 6.6.6.6/32 | 6         | 1     | 6.6.6.6/32  | N       |   SD    | e2e_R4_1          | 128        |
	| 7.7.7.7/32 | 7         | 1     | 7.7.7.7/32  | N       |   SD    | e2e_R4_1          | 128        |
	| 8.8.8.8/32 | 8         | 1     | 8.8.8.8/32  | N       |   SD    | e2e_R4_1          | 128        |
	Total mapping entries: 3
	
	Level 2:
	Active Binding-SIDs:
	| Prefix     | SID index | Range | Last Prefix | P-Flags | B-Flags | Advertised System | Preference |
	+------------+-----------+-------+-------------+---------+---------+-------------------+------------+
	| 6.6.6.6/32 | 6         | 1     | 6.6.6.6/32  | N       |   S     | e2e_R1_1          | 128        |
	| 7.7.7.7/32 | 7         | 1     | 7.7.7.7/32  | N       |   S     | e2e_R1_1          | 128        |
	| 8.8.8.8/32 | 8         | 1     | 8.8.8.8/32  | N       |   S     | e2e_R1_1          | 128        |
	Total mapping entries: 3

	dnRouter# show isis segment-routing prefix-sid-map backup

	Instance INSTANCE_1
	Backup Binding-SIDs:
	
	Total mapping entries: 0

.. **Help line:** Display the received prefix-sid-map mapping

**Command History**

+---------+-------------------------------------------------------------------+
| Release | Modification                                                      |
+=========+===================================================================+
| 14.0    | Command introduced                                                |
+---------+-------------------------------------------------------------------+
| 15.0    | Added P-Flags, B-Flags, and mapping server to the command output. |
+---------+-------------------------------------------------------------------+


