system debug file files
-------------------------

**Minimum user role:** operator

By default, the system saves 10 debug messages local log files. You can change this limit, depending on the space that you can allocate to logging.

To set the number of log files:

**Command syntax: files [files]**

**Command mode:** config

**Hierarchies**

- system debug


.. **Note**

	- "no debug" command reverts the whole debug paramets to its default value

	- "no debug file" command reverts the debug file parameter to its default value

	- "no debug file <file-name>" reverts the debug file parameter to its default value

	- "no debug file <file-name> files" reverts configuration of number of rotated files per specific debug file to its default.

	- After maximum number of files is reached, the oldest file is overwritten


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                                                                         | Range | Default |
+===========+=====================================================================================================================================================+=======+=========+
| Files     | The maximum number of log files that the system will create. When the number is reached and the last file is full, the oldest file will be deleted. | 1..20 | 10      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp 
	dnRouter(system-debug-file-bgp)# files 20
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-debug-file-bgp)# no files 

.. **Help line:** configure number of rotated files for debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


