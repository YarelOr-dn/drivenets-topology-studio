set cli-timestamp 
------------------

**Minimum user role:** viewer

By default, commands displayed in the CLI do not show a timestamp. To turn on timestamp so that each entered command will be displayed with a timestamp:

**Command syntax: set cli-timestamp**

**Command mode:** operational

**Example**
::

	dnRouter# set cli-timestamp
	
	dnRouter(cfg 08-Aug-2017-17:16:08)# show system version
	
	System Name: dnRouter
	Version: DNOS [4.1]
	
	dnRouter(08-Aug-2017-17:16:08)# show system version
	
	System Name: dnRouter
	Version: DNOS [4.1]
	
	dnRouter(cfg 08-Aug-2017-17:16:08)# system name my_name
	my_name(cfg)#	

**Removing Configuration**

To disable the CLI timestamp:
::

	dnRouter# unset cli-timestamp


.. **Help line:** Set timestamp to the CLI prompt

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 5.1.0       | Command introduced                           |
+-------------+----------------------------------------------+
|             |                                              |
| 6.0         | Changed from run command to set command      |
+-------------+----------------------------------------------+
|             |                                              |
| 10.0        | Changed the syntax from disabled to unset    |
+-------------+----------------------------------------------+