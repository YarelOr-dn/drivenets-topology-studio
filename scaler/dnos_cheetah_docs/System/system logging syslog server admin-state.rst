system logging syslog server admin-state
----------------------------------------

**Minimum user role:** operator

To enable or disable the remote syslog server:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system logging syslog


.. **Note**

	- no command set admin-state to the default value

	- when syslog-server admin-state is set to disabled, system-events are not exported to this syslog server

**Parameter table**

+-------------+-------------------------------------------------------------------------------------------------------------------------------------+----------+---------+
| Parameter   | Description                                                                                                                         | Range    | Default |
+=============+=====================================================================================================================================+==========+=========+
| admin-state | Sets the administrative state of the remote syslog server. When disabled, system events will not be exported to this syslog server. | Enabled  | Enabled |
|             |                                                                                                                                     | Disabled |         |
+-------------+-------------------------------------------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog-server)# admin-state disabled 
	
	

**Removing Configuration**

To disable the syslog server:
::

	dnRouter(system-logging-syslog-server)# no admin-state 

.. **Help line:** Configure syslog server admin-state

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+
| 11.0    | Applied new hierarchy |
+---------+-----------------------+


