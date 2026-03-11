show system hardware fan
------------------------

**Minimum user role:** viewer

To display information on the system's fan resources:



**Command syntax: show system hardware fan** [node-name] [node-id]

**Command mode:** operational



**Note**

- FAIL status indicates fan speed is lower threshold. Uptime indicates how long the fan has status OK.

- By default, if a node name is not specified, the output will show all the nodes in the DNOS cluster.

.. - By default (if node name not specified), output will show all the nodes in DNOS cluster.

	- FAIL status indicates fan speed is lower threshold. Uptime indicates how long the fan has status OK.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Parameter | Description                                                                                                                                | Range               |
+===========+============================================================================================================================================+=====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP, NCF, NCC, NCM  |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..249         |
|           |                                                                                                                                            | NCC: 0..1           |
|           |                                                                                                                                            | NCF: 0..611         |
|           |                                                                                                                                            | NCM: A0-1, B0-1     |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+



**Example**
::

	dnRouter# show system hardware fan
	
	ncp 0 (dn-ncp-0)
	
	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime             |
	  |----------+---------+--------+-------------+---------+-------|--------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   |  30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   |  30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   |   2 days, 17:26:09 |
	  | 4        | YES     | FAIL   |             |         |       |                    |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   |  30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                    |
	
	ncf 0 (dn-ncf-0)
	
	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime             |
	  |----------+---------+--------+-------------+---------+-------|--------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   |  30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   |  30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   |  30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   |   5 days, 12:25:09 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   |  30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                    |


	dnRouter# show system hardware fan ncp 5
	
	ncp 5 (dn-ncp-5)
	
	Fans:
	  Redundancy mode: 3+1
	  | Fan ID   | Present | Status | Speed [RPM] | Max RPM | RPM % | Uptime             |
	  |----------+---------+--------+-------------+---------+-------|--------------------|
	  | 1        | YES     | OK     | 9000        | 18000   | 50%   |  30 days, 04:35:06 |
	  | 2        | YES     | OK     | 10000       | 20000   | 50%   |  30 days, 04:35:06 |
	  | 3        | YES     | OK     | 10000       | 20000   | 10%   |  30 days, 04:35:06 |
	  | 4        | YES     | OK     | 9000        | 20000   | 20%   |   5 days, 12:25:09 |
	  | PSU0     | YES     | OK     | 9000        | 20000   | 10%   |  30 days, 04:35:06 |
	  | PSU1     | YES     | FAIL   |             |         |       |                    |

	
	

.. **Help line:** show system hardware fan information

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 7.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 10.0    | Updated syntax to reflect the new NCR architecture. |
+---------+-----------------------------------------------------+
| 13.1    | Added uptime                                        |
+---------+-----------------------------------------------------+
