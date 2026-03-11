system debug file
-----------------

**Minimum user role:** operator

Configure debug messages logging to local files. Debug messages are generated for debugging purposes and are stored in local files.

To configure logging of debug messages to local files:

**Command syntax: system debug file [file-name]**

**Command mode:** config

**Hierarchies**

- system debug


**Note**

- Debug messages are much more volume intensive than system events.

- Notice the change in prompt.

- If a newly configured debug file already exists in the file system, the debug data will be appended to the existing file.

.. - "no debug" command reverts the whole debug paramets to its default value

	- "no debug file <file-name>" command reverts the debug file parameter to its default value

**Parameter table**

+-----------+-----------------------------+--------------------+---------+
| Parameter | Description                 | Range              | Default |
+===========+=============================+====================+=========+
| file-name | The debug file to configure | Any system process | \-      |
+-----------+-----------------------------+--------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# debug
	dnRouter(cfg-system-debug)# file bgp
	dnRouter(system-debug-file-bgp)#




**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-debug)# no file bgp
	dnRouter(cfg-system)# no debug

.. **Help line:** configure debug messages logging to local files.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


