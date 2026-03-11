system logging syslog timestamp-format utc-normalize
----------------------------------------------------

**Minimum user role:** operator

Specifies if generated system-events timestamp format will be normalized based on the UTC time-zone or based on the configured system time-zone. When enabled, timestamp will be normalized based on the UTC time-zone.

**Command syntax: utc-normalize [admin-state]**

**Command mode:** config

**Note:**

- The 'no' command returns to the default value.

**Help line:** Configure timestamp UTC normalization

**Parameter table:**

+------------------+---------------------+---------------+
| Parameter        | Values              | Default value |
+==================+=====================+===============+
| admin-state      | enabled, disabled   | enabled       |
+------------------+---------------------+---------------+

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# timestamp-format
	dnRouter(cfg-logging-syslog-timestamp)# utc-normalize enabled


	dnRouter(cfg-logging-syslog-timestamp)# no utc-normalize

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+

