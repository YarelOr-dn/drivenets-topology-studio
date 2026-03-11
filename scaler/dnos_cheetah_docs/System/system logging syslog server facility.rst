system logging syslog server facility
-------------------------------------

**Minimum user role:** operator

To override the global Syslog facility configuration on a per server basis.

**Command syntax: facility [facility]**

**Command mode:** config

**Hierarchies**

- system logging syslog server

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter | Description                                                                      | Range             | Default |
+===========+==================================================================================+===================+=========+
| facility  | Facility code which overrides the globally configured syslog facility on a per   | | kern            | \-      |
|           | server basis                                                                     | | user            |         |
|           |                                                                                  | | mail            |         |
|           |                                                                                  | | system-daemon   |         |
|           |                                                                                  | | auth            |         |
|           |                                                                                  | | syslog          |         |
|           |                                                                                  | | lpr             |         |
|           |                                                                                  | | news            |         |
|           |                                                                                  | | uucp            |         |
|           |                                                                                  | | cron            |         |
|           |                                                                                  | | authpriv        |         |
|           |                                                                                  | | ftp             |         |
|           |                                                                                  | | ntp             |         |
|           |                                                                                  | | log-alert       |         |
|           |                                                                                  | | local0          |         |
|           |                                                                                  | | local1          |         |
|           |                                                                                  | | local2          |         |
|           |                                                                                  | | local3          |         |
|           |                                                                                  | | local4          |         |
|           |                                                                                  | | local5          |         |
|           |                                                                                  | | local6          |         |
|           |                                                                                  | | local7          |         |
+-----------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dev-dnRouter(cfg)# system
    dev-dnRouter(cfg-system)# logging
    dev-dnRouter(cfg-system-logging)# syslog
    dev-dnRouter(cfg-system-logging-syslog)# server 1.1.1.1 vrf default
    dev-dnRouter(cfg-logging-syslog-server)# facility auth


**Removing Configuration**

To revert the facility per server configuration to default:
::

    dev-dnRouter(cfg-logging-syslog-server)# no facility

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
