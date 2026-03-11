system logging syslog 
----------------------

**Minimum user role:** operator

You can manage which log files will be sent to a remote syslog server. See system logging syslog server for details on configuring a syslog server.

To enter the syslog configuration mode:

**Command syntax: syslog**

**Command mode:** config

**Hierarchies**

- system logging 


**Note**

- Notice the change in prompt

.. - no command reverts all the syslog parameters back to the default


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-logging)# no syslog

.. **Help line:** enters to syslog hierarchy for system-events.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


