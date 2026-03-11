debug bgp
----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug BGP events:

**Command syntax: bgp** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all bgp events will be debugged.

- Each command can be negated using the no or unset command prefix.

-  The debug information is written in the bgpd log file.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

**Parameter table**

+-------------------+------------------------------------------------------------+
| Parameter         | Description                                                |
+===================+============================================================+
| as4               | Debug bgp AS4 actions                                      |
+-------------------+------------------------------------------------------------+
| as4-segment       | Debug BGP AS4 path segment handling                        |
+-------------------+------------------------------------------------------------+
| best-path         | Debug BGP best-path                                        |
+-------------------+------------------------------------------------------------+
| bfd               | Debug BGP-BFD events                                       |
+-------------------+------------------------------------------------------------+
| BMP-general       | Debug BMP Monitoring general events                        |
+-------------------+------------------------------------------------------------+
| BMP-session       | Debug BMP session related event protocol state and packets |
+-------------------+------------------------------------------------------------+
| events            | Debug BGP events                                           |
+-------------------+------------------------------------------------------------+
| export            | Debug BGP export actions                                   |
+-------------------+------------------------------------------------------------+
| filters           | Debug BGP filters                                          |
+-------------------+------------------------------------------------------------+
| fsm               | Debug BGP finite state machine                             |
+-------------------+------------------------------------------------------------+
| import            | Debug BGP import actions                                   |
+-------------------+------------------------------------------------------------+
| keepalives        | Debug BGP keepalives                                       |
+-------------------+------------------------------------------------------------+
| leak              | Debug BGP leak actions                                     |
+-------------------+------------------------------------------------------------+
| nht               | Debug BGP next hop tracking events                         |
+-------------------+------------------------------------------------------------+
| nsr               | Debug BGP non-stop routing                                 |
+-------------------+------------------------------------------------------------+
| rib               | Debug BGP-RIB messages                                     |
+-------------------+------------------------------------------------------------+
| rpki              | Debug BGP RPKI                                             |
+-------------------+------------------------------------------------------------+
| rtr               | Debug BGP RTR protocol                                     |
+-------------------+------------------------------------------------------------+
| updates-in        | Debug BGP updates in                                       |
+-------------------+------------------------------------------------------------+
| updates-out       | Debug BGP updates out                                      |
+-------------------+------------------------------------------------------------+
| internal-tasks    | Debug BGP internal processing tasks                        |
+-------------------+------------------------------------------------------------+
| update-group      | Debug BGP update-group object management                   |
+-------------------+------------------------------------------------------------+
| process-scheduled | Debug BGP processing                                       |
+-------------------+------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# bgp as4
	dnRouter(cfg-debug)# bgp as4-segment
	dnRouter(cfg-debug)# bgp filters
	dnRouter(cfg-debug)# bgp fsm
	dnRouter(cfg-debug)# bgp
	dnRouter(cfg-debug)# bgp updates-in
	dnRouter(cfg-debug)# bgp updates-out
	dnRouter(cfg-debug)# debug bgp updates-out

**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no bgp as4-segment
	dnRouter(cfg-debug)# no bgp as4
	dnRouter(cfg-debug)# no bgp filters
	dnRouter(cfg-debug)# no bgp fsm
	dnRouter(cfg-debug)# no bgp


.. **Help line:** Debug BGP events

**Command History**

+---------+---------------------------------------------------------------------------+
| Release | Modification                                                              |
+=========+===========================================================================+
| 6.0     | Command introduced                                                        |
+---------+---------------------------------------------------------------------------+
| 7.0     | Updated the non-persistent debug logging command to a "set" command.      |
+---------+---------------------------------------------------------------------------+
| 10.0    | Replaced "no set" with "unset"                                            |
+---------+---------------------------------------------------------------------------+
| 11.5    | Renamed "general-events" as "internal-tasks", applied new debug hierarchy |
+---------+---------------------------------------------------------------------------+
| 13.0    | Added debug parameters update-group, process-scheduled, and nsr           |
+---------+---------------------------------------------------------------------------+
| 15.1    | Added debug parameters best-path, rpki, rtr, bmp-general and bmp-session  |
+---------+---------------------------------------------------------------------------+
| 16.2    | Removed set-debug command                                                 |
+---------+---------------------------------------------------------------------------+