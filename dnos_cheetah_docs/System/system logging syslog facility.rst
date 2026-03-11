system logging syslog facility
------------------------------

**Minimum user role:** operator

To configure the facility to which the system log messages belongs:

**Command syntax: facility [syslog-facility]**

**Command mode:** config

**Hierarchies**

- system logging syslog


.. **Note**

	- no command set facility to the default value

**Parameter table**

+-----------------+-------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter       | Description                                                                   | Range                                                                                                                                                                                        | Default |
+=================+===============================================================================+==============================================================================================================================================================================================+=========+
| syslog-facility | The code that specifies the facility to which the system log message belongs. | kern, user, mail, system-daemon, auth, syslog, lpr, news, uucp, cron, authpriv, ftp, ntp, log-alert, local0, local1, local2, local3, local4, local5, local6, local7                          | local7  |
+-----------------+-------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# facility local0



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-logging-syslog)# no facility

.. **Help line:** Configure syslog server facility

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                |
+=========+=============================================================================================================================+
| 5.1.0   | Command introduced                                                                                                          |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                                                                                       |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Applied new hierarchy                                                                                                       |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Removed from the server hierarchy to global syslog hierarchy and changed the syntax from "server-facility " to "facility"   |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
| 11.5    | Renamed the daemon, security, console, and solaris-cron facilities as system-daemon, log-audit, log-alert, and clock-daemon |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
| 19.1    | Removed unsupported facilities log-audit and clock-daemon                                                                   |
+---------+-----------------------------------------------------------------------------------------------------------------------------+
