show system hardware power
--------------------------

**Minimum user role:** viewer

To display system hardware power for the cluster nodes:



**Command syntax: show system hardware power** [node-name] [node-id] detail

**Command mode:** operational



**Note**

- Status "Fail" is displayed when the internal IPMI output is 0.

.. - By default (if ncp not specified), output will show all the nodes in DNOS cluster.

	- Status failed will be shown when the internal ipmi output is 0. Uptime indicates how long the PSU has status OK.

**Parameter table**

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Parameter | Description                                                                                                                                | Range               |
+===========+============================================================================================================================================+=====================+
| node-name | The name of the node used to filter the output to a specific cluster element. If no name is provided, all cluster nodes will be displayed. | NCP, NCF, NCC       |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| node-id   | The ID of the node used to filter the output to a specific cluster element.                                                                | NCP: 0..249         |
|           |                                                                                                                                            | NCC: 0..1           |
|           |                                                                                                                                            | NCF: 0..611         |
|           |                                                                                                                                            | NCM: A0-A1, B0-B1   |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| uptime    | Uptime indicates how long the PSU has status OK                                                                                            | dddd days, hh:mm:ss |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------+---------------------+

**Example**
::

	dnRouter# show system hardware power 
	
	ncp 0 (dn-ncp-0) 
	Power Supply Units:
	Redundancy mode: 1+1
	| PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	|----------+-----------+----------+---------------------+------------+---------|-------------------|
	| 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | AC 220V |                   |
	| 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |
	
	
	dnRouter# show system hardware power detail
	
	ncp 0 (dn-ncp-0)
	Power Supply Units:
	Redundancy mode: 1+1
	| PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	|----------+-----------+----------+---------------------+------------+---------|-------------------|
	| 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | AC 220V |                   |
	| 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |

	PSU 0:
	  input power: 48V input
	  Capacity: 3500W (maximum 3500 W)
	  DC output: 410W (9A at 57V, 20% of capacity)
	PSU 1:
	  input power: 48V input
	  Capacity: 3500W (maximum 3500 W)
	  DC output: 410W (9A at 57V, 20% of capacity)
	node:
	  Total capacity: 3500W (maximum 3500 W)
	  Total remaining: 2000W 
	
	dnRouter# show system hardware power ncp 5 detail
	
	ncp 5 (dn-ncp-5)
	Power Supply Units:
	Redundancy mode: 1+1
	| PSU ID   | Present   | Status   | Serial              | Revision   | Type    | Uptime            |
	|----------+-----------+----------+---------------------+------------+---------|-------------------|
	| 0        | YES       | FAIL     | S0B000Z851924001590 | AM-2A02P10 | AC 220V |                   |
	| 1        | YES       | OK       | S0B000Z851924001601 | AM-2A02P10 | AC 220V | 30 days, 04:35:06 |

	PSU 0:
	  input power: 48V input
	  Capacity: 3500W (maximum 3500 W)
	  DC output: 410W (9A at 57V, 20% of capacity)
	PSU 1:
	  input power: 48V input
	  Capacity: 3500W (maximum 3500 W)
	  DC output: 410W (9A at 57V, 20% of capacity)
	node:
	  Total capacity: 3500W (maximum 3500 W)
	  Total remaining: 2000W 

	dnRouter# show system hardware power ncm A0 detail
	
	ncm A0 (dn-ncm-A0)
	Power Supply Units:
	Redundancy mode: None
	| PSU ID   | Present   | Status   | Serial             | Revision   | Type         | Uptime            |
	|----------+-----------+----------+--------------------+------------+--------------|-------------------|
	| 0        | YES       | FAIL     | TA000X131920000013 | 1.0        | AC 100-240 V |                   |
	| 1        | YES       | OK       | TA000X131920000011 | 1.0        | AC 100-240 V | 30 days, 04:35:06 |
	PSU 0:
		input power: 0V
		Capacity: 0.0W (Maximum 0.0W)
		DC output: 0W (0A at 0V, 0% of capacity)
	PSU 1:
		input power: 0V
		Capacity: 850.0W (Maximum 850.0W)
		DC output: 179W (14A at 12V, 21% of capacity)
	node:
		Total capacity: 850W (maximum 850W)
		Total remaining: 671W
	

.. **Help line:** show system hardware power information

**Command History**

+---------+----------------------------------------------------+
| Release | Modification                                       |
+=========+====================================================+
| 7.0     | Command introduced                                 |
+---------+----------------------------------------------------+
| 10.0    | Updated syntax to reflect the new NCR architecture |
+---------+----------------------------------------------------+
| 11.6    | Added Uptime                                       |
+---------+----------------------------------------------------+
