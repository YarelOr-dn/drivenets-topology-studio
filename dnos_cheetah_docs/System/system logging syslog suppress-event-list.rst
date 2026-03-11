system logging syslog suppress-event-list
-----------------------------------------

**Minimum user role:** operator

The suppress-event-list is a list of system events that you do not want DNOS to generate.

To add a system event to the suppress-event-list:

**Command syntax: suppress-event-list [suppress-event-name]**

**Command mode:** config

**Hierarchies**

- system logging syslog

.. **Note**

	-  no command removes the event from suppress-list

**Parameter table**

+------------+--------------------------------------------------------------------+-----------+---------+
| Parameter  | Description                                                        | Range     | Default |
+============+====================================================================+===========+=========+
| event-name | State the name of the event that you do not want DNOS to generate. | Any event | \-      |
+------------+--------------------------------------------------------------------+-----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# suppress-event-list BGP_NEIGHBOR_MAXIMUM_PREFIX_THRESHOLD_EXCEEDED
	
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-logging-syslog)# no suppress-event-list BGP_NEIGHBOR_MAXIMUM_PREFIX_THRESHOLD_EXCEEDED

.. **Help line:** add system-event to the events suppress-list.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


