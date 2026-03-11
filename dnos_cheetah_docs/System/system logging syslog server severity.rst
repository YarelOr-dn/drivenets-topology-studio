system logging syslog server severity
-------------------------------------
**Minimum user role:** operator

Configure the severity per syslog server.

The default severity per syslog server is warning. You can change the severity to emergency, criticial, error, warning, notification, info, and debug.

To configure the severity per syslog server:

**Command syntax: severity [severity]**

**Command mode:** config

**Note**

- The 'no' command sets the severity to the default value.

**Parameter table**

+-----------+-----------------------------------+----------------+--------------+
| Parameter | Description                       | Range          | Default      |
+===========+===================================+================+==============+
| severity  | Set severity per syslog server.   | emergency      | warning      |
|           |                                   | critical       |              |
|           |                                   | error          |              |
|           |                                   | warning        |              |
|           |                                   | notification   |              |
|           |                                   | info           |              |
|           |                                   | debug          |              |
+-----------+-----------------------------------+----------------+--------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog-server)# severity info

	dnRouter(system-logging-syslog-server)# no severity

**Help line:** configure severity per syslog server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
