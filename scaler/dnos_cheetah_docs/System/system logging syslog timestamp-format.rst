system logging syslog timestamp-format
--------------------------------------
**Minimum user role:** operator

Configure the timestamp UTC normalization.
Define how the timestamp is printed in the system-events syslogs.

**Command syntax: timestamp-format**

**Command mode:** config

**Note:**

- The 'no' command returns all configuration under timestamp-format to their default settings.

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# timestamp-format
	dnRouter(cfg-logging-syslog-timestamp)#


	dnRouter(cfg-system-logging-syslog)# no timestamp-format

**Help line:** Configure timestamp UTC normalization

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
