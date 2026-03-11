show file log
-------------

**Minimum user role:** viewer

To display a log file:



**Command syntax: show file** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} **log [ file-name ]** severity [severity]

**Command mode:** operational



**Note**

- If you do not specify a file to display, the log files from the active NCC is displayed by default.

..
	**Internal Note**

	- by default display log files from active NCC

	- show file should provide access only to specific folders where the files exist

	- pressing tab should provide the list of available files in the folder

	- master log file for each process should have alias name without the file extension ".log". i.e "show file ldp" instead "show file ldp.log". This is relevant ONLY to the master file name of each process (not the rotated files)


**Parameter table**

+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| Parameter | Description                                                                                 | Range          | Default |
+===========+=============================================================================================+================+=========+
| ncc-id    | Filters the displayed information to the specified NCC.                                     | 0..1           | \-      |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| ncp-id    | Filters the displayed information to the specified NCP.                                     | 0..191         | \-      |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| ncf-id    | Filters the displayed information to the specified NCF.                                     | 0..12          | \-      |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| ncm-id    | Filters the displayed information to the specified NCM.                                     | a0, b0, a1, b1 | \-      |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| file-name | The name of the file to display. Click on the Tab key to display a list of available files. | \-             | \-      |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+
| severity  | Set the minimum severity of logs to be displayed.                                           | emergency      | debug   |
|           |                                                                                             | critical       |         |
|           |                                                                                             | error          |         |
|           |                                                                                             | warning        |         |
|           |                                                                                             | notification   |         |
|           |                                                                                             | info           |         |
|           |                                                                                             | debug          |         |
+-----------+---------------------------------------------------------------------------------------------+----------------+---------+

**Example**
::

	dnRouter# show file ncc 0 log ldp

	dnRouter# show file ncp 0 log ldp severity info

.. **Help line:** show file

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+


