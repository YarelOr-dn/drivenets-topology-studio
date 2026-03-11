show isis traffic-engineering database
--------------------------------------

**Minimum user role:** viewer

To display the IS-IS traffic-engineering database:



**Command syntax: show isis** instance [isis-instance-name] **traffic-engineering database** router-id [router-id]

**Command mode:** operational



.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------+
| Parameter          | Description                                                        |
+====================+====================================================================+
| No filter          | Displays the entire traffic-engineering database.                  |
+--------------------+--------------------------------------------------------------------+
| isis-instance-name | Filters the displayed information for the specified IS-IS instance |
+--------------------+--------------------------------------------------------------------+
| router-id          | Filters the information for a specific router-id.                  |
+--------------------+--------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis traffic-engineering database 
	level-1:
	level-2:
	1.1.1.1 -->  2.2.2.2
	  Local address: 12.3.0.10/0
	  Remote address: 12.3.0.2/0
	  Connectivity type: isis broadcast
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	1.1.1.1 -->  3.3.3.3
	  Local address: 12.3.0.10/0
	  Remote address: 12.3.0.3/0
	  Connectivity type: isis broadcast
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	1.1.1.1 -->  3.3.3.3
	  Local address: 13.0.0.10/0
	  Remote address: 13.0.0.3/0
	  Connectivity type: isis poit-to-point
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	2.2.2.2 -->  1.1.1.1
	  Local address: 12.3.0.2/0
	  Remote address: 12.3.0.10/0
	  Connectivity type: isis broadcast
	  Metric: 10
	  Affinity: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	dnRouter# show isis traffic-engineering database router-id 1.1.1.1
	level-1:
	level-2:
	1.1.1.1 -->  2.2.2.2
	  Local address: 12.3.0.10/0
	  Remote address: 12.3.0.2/0
	  Connectivity type: isis broadcast
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	1.1.1.1 -->  3.3.3.3
	  Local address: 12.3.0.10/0
	  Remote address: 12.3.0.3/0
	  Connectivity type: isis broadcast
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	1.1.1.1 -->  3.3.3.3
	  Local address: 13.0.0.10/0
	  Remote address: 13.0.0.3/0
	  Connectivity type: isis poit-to-point
	  Metric: 10
	  Admin-group: 0x0
	  Max BW: 10000
	  Max Rsrv BW: 10000
	  Unreserved BW: 
	   [0] 10000   [1] 10000
	   [2] 10000   [3] 10000
	   [4] 10000   [5] 10000
	   [6] 10000   [7] 10000
	
	dnRouter# show isis instance CORE traffic-engineering database router-id 1.1.1.1
	
	

.. **Help line:**

**Command History**

+---------+---------------------------------+
| Release | Modification                    |
+=========+=================================+
| 9.0     | Command introduced              |
+---------+---------------------------------+
| 10.0    | Added filter per IS-IS instance |
+---------+---------------------------------+


