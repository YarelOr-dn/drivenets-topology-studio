show system hardware temperature
--------------------------------

**Minimum user role:** viewer

This command displays system hardware temperature information per node in the DNOS cluster. The threshold values are determined by the hardware vendor. "Fan 100% User threshold" indicates the temperature threshold for the supported sensor where the node fans reach 100% speed.

To display system hardware temperature:



**Command syntax: show system hardware temperature** [node-name] [node-id]

**Command mode:** operational



**Note**

- The thresholds are supported according to the hardware vendor support.

- The temperature is displayed in degrees Celsius.

.. - By default (if ncp not specified), output will show all the nodes in DNOS cluster.

	- WARNING-LOW and CRITCAL-LOW statuses supported according to the hardware vendor support.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Parameter | Description                                                                                                                                | Range               |
+===========+============================================================================================================================================+=====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP                 |
|           |                                                                                                                                            | NCF                 |
|           |                                                                                                                                            | NCC                 |
|           |                                                                                                                                            | NCM                 |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..249         |
|           |                                                                                                                                            | NCC: 0..1           |
|           |                                                                                                                                            | NCF: 0..611         |
|           |                                                                                                                                            | NCM: A0, A1, B0, B1 |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+

The following are the possible statuses:

+---------------+-----------------------------------------------------------------------------+
| Status        | Description                                                                 |
+===============+=============================================================================+
| Fail          | No reading                                                                  |
+---------------+-----------------------------------------------------------------------------+
| OK            | The temperature is within normal range                                      |
+---------------+-----------------------------------------------------------------------------+
| WARNING-HIGH  | The temperature has crossed the High Warning Threshold (vendor dependent).  |
+---------------+-----------------------------------------------------------------------------+
| CRITICAL-HIGH | The temperature has crossed the High Critical Threshold (vendor dependent). |
+---------------+-----------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system hardware temperature
	
	ncp 0 (dn-ncp-0)

	Temperature alarm raised: True (WARNING)

    Temperature Sensors:
	  | Sensor Name   | Temperature [C] | Status | High Warning | High Critical | Fan 100%           |
	  |               |                 |        | Threshold [C]| Threshold [C] | User Threshold [C] |
	  |---------------+-----------------+--------+--------------+---------------+--------------------|
	  | TEMP_BMC      | 23              | OK     | 60           | 75            | N/A                |
	  | TEMP_BOARD1   | 65              | WARN   | 60           | 75            | N/A                |
	  | TEMP_BOARD2   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_L   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC1_R   | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_L   | 40              | OK     | 60           | 75            | N/A                |
	  | TEMP_MAC2_R   | 24              | OK     | 60           | 75            | N/A                |
	  | TEMP_QSFP1    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_QSFP2    | 24              | OK     | 65           | 80            | N/A                |
	  | TEMP_CPU_PECI | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU1     | 38              | OK     | 60           | 75            | N/A                |
	  | TEMP_PSU0     | 38              | OK     | 60           | 75            | N/A                |
	
	dnRouter# show system hardware temperature ncp 5
	
	ncp 5 (dn-ncp-5)

	Temperature alarm raised: False

    Temperature Sensors:

	  | Sensor Name     | Temperature [C]   | Status   | High Warning    | High Critical   | Fan 100%           |
	  |                 |                   |          | Threshold [C]   | Threshold [C]   | User Threshold [C] |
	  |-----------------+-------------------+----------+-----------------+-----------------+--------------------|
	  | PSU1_T_Ambient  | 33.0              | OK       | 60              | 65              | N/A                |
	  | PSU1_T_Hotsport | 49.0              | OK       | 75              | 90              | N/A                |
	  | PSU2_T_Ambient  | 30.0              | OK       | 60              | 65              | N/A                |
	  | PSU2_T_Hotsport | 31.0              | OK       | 75              | 90              | N/A                |
	  | Temp_CPUB       | 41.0              | OK       | 80              | 85              | N/A                |
	  | Temp_DB_3V3     | 26.0              | OK       | 130             | 134             | 117                |
	  | Temp_Hot_Spot   | 35.0              | OK       | 75              | 80              | N/A                |
	  | Temp_MAC0_DN    | 57.0              | OK       | 105             | 110             | N/A                |
	  | Temp_MAC0_UP    | 59.0              | OK       | 105             | 110             | 90                 |
	  | Temp_Main_Front | 35.0              | OK       | 60              | 65              | N/A                |
	  | Temp_Main_KBP   | 32.0              | OK       | 95              | 100             | N/A                |
	  | Temp_Main_Rear  | 35.0              | OK       | 60              | 65              | N/A                |

  	dnRouter# show system hardware temperature ncm A0

	ncm A0 (dn-ncm-A0)

    Temperature Sensors:
	  | Sensor Name            | Temperature [C]   | Status   | High Warning    | High Critical   | Fan 100%           |
	  |                        |                   |          | Threshold [C]   | Threshold [C]   | User Threshold [C] |
	  |------------------------+-------------------+----------+-----------------+-----------------+--------------------|
	  | LM75_1: Main Board U39 | 22.0              | OK       | 55              | 60              | N/A                |
	  | LM75_2: Main Board U50 | 19.0              | OK       | 55              | 60              | N/A                |
	  | LM75_3: Main Board U35 | 24.0              | OK       | 55              | 60              | N/A                |
	  | LM75_4: CPU Board U20  | 21.0              | OK       | 55              | 60              | N/A                |
	

.. **Help line:** show system hardware temperature information

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 7.0     | Command introduced                                 |
+---------+----------------------------------------------------+
| 10.0    | Updated syntax to reflect the new NCR architecture |
+---------+----------------------------------------------------+
| 18.1    | Added temperature alarm indication                 |
+---------+----------------------------------------------------+

