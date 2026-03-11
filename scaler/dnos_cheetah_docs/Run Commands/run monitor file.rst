run monitor file 
-----------------

**Minimum user role:** viewer

The run monitor file command enables to monitor live output of a selected file.

**Command syntax: run monitor file** { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] } **[file-type] [file-name]**

**Command mode:** operation 

**Note**

- If you do not specify an NCE, the file from the active NCC will be monitored.

.. - monitor file should provide access only to specific folders where the files exist

	- The user should not have access to other folders

	- pressing tab should provide the list of available files in the folder

	- Each file type has a different location

	- master log file for each process should have alias name without the file extension ".log. i.e "run monitor file ldp" instead "run monitor file ldp.log". This is relevant ONLY to the master file name of each process (not the rotated files )

	- If no ncc-id/ncp-id/ncf-id was specified, the command relates to the active NCC

	- Each file type has a different location:

	- log - /var/log/dn/

	- traces - /var/log/dn/traces

	- file types to show files on NCCs:

	- log

	- traces - /var/log/dn/traces

	- file types to show files on NCPs/NCFs:

	- log

	- traces - /var/log/dn/traces

**Parameter table**

+-----------+----------------------------------------------------+--------+
| Parameter | Description                                        | Range  |
+===========+====================================================+========+
| ncc-id    | Monitors the file from the specified NCC           | 0..1   |
+-----------+----------------------------------------------------+--------+
| ncp-id    | Monitors the file from the specified NCP           | 0..191 |
+-----------+----------------------------------------------------+--------+
| ncf-id    | Monitors the file from the specified NCF           | 0..12  |
+-----------+----------------------------------------------------+--------+
| file-type | Specify the type of file that you want to monitor. | Log    |
|           |                                                    | Traces |
+-----------+----------------------------------------------------+--------+
| file-name | The name of the file you want to monitor.          | String |
+-----------+----------------------------------------------------+--------+

**Example**
::

	dnRouter# run monitor file log ldp
	
	dnRouter# run monitor file ncp 0 log bfd  
	

.. **Help line:** monitor file

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 5.1.0   | Command introduced                                |
+---------+---------------------------------------------------+
| 10.0    | Command not supported                             |
+---------+---------------------------------------------------+
| 11.0    | Added option to monitor files from a specific NCE |
+---------+---------------------------------------------------+


