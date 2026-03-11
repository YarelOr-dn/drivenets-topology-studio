show bmp server summary
-----------------------

**Minimum user role:** viewer

The following command displays a summary of a bmp session information:

**Command syntax: show bmp server summary**

**Command mode:** operational



.. **Note**


The following BMP server information is displayed:

+-----------+----------------------------------------------------------------------------------+
| Parameter | Description                                                                      |
+===========+==================================================================================+
| ID        | The configured BMP server-id                                                     |
+-----------+----------------------------------------------------------------------------------+
| Host      | The configured BMP server host IP address                                        |
+-----------+----------------------------------------------------------------------------------+
| Port      | The configured BMP server destination TCP port                                   |
+-----------+----------------------------------------------------------------------------------+
| VRF       | The configured BMP server VRF instance                                           |
+-----------+----------------------------------------------------------------------------------+
| State     | The BMP session state (Up, Down or Admin-down)                                   |
+-----------+----------------------------------------------------------------------------------+
| Time      | The amount of time the BMP server is in its current state                        |
+-----------+----------------------------------------------------------------------------------+
| NBRs      | Number of established BGP neighbors for which the BMP activate-server is enabled |
+-----------+----------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show bmp server summary

	| ID    | Host          | Port   | Vrf       | State      | Time       | NBRs    |
	|-------+---------------+--------+-----------+------------|------------|---------|
	| 0     | 100.64.0.163  |   5000 | default   | Up         | 45m18s     |       4 |
	| 2     | 202.202.88.8  |   5001 | default   | Down       | 01m06s     |       2 |
	| 4     | 1:1::1:1      |   8000 | default   | Admin-down | 01m06s     |       2 |

.. **Help line:** displays bmp session information

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+


