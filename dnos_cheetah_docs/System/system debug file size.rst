system debug file size
------------------------

**Minimum user role:** operator

**Description:** 


**Command syntax: size [size]**

**Command mode:** config

**Hierarchies**

- system debug


.. **Note**

	- "no debug" command reverts the whole debug paramets to its default value

	- "no debug file <file-name>" reverts the debug file parameter to its default value

	- "no debug file <file-name> size" removes configuration of rotated files size per specific debug file to default.

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------+------------+---------+
| Parameter | Description                                                                                   | Range      | Default |
+===========+===============================================================================================+============+=========+
| Size      | The maximum size of the file. When the size is reached, new logs will be saved in a new file. | 1..1024 MB | 10 MB   |
+-----------+-----------------------------------------------------------------------------------------------+------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp
	dnRouter(system-debug-file-bgp)# size 3

	dnRouter(cfg-system-debug)# file ospf
	dnRouter(system-debug-file-ospf)# size 5


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-debug-file-bgp)# no size
	dnRouter(cfg-system-debug)# no file bgp


.. **Help line:** configure maximum number of the logging file for debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


