debug ldp
----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug LDP events:

**Command syntax: ldp** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all ldp events will be debugged.

- Each command can be negated using the no or unset command prefix.

- The debug information is written in the ldpd log file.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.


**Parameter table**

+------------------+-------------------------------------------------+
| Argument         | Description                                     |
+==================+=================================================+
| bindings         | Debug LDP bindings                              |
+------------------+-------------------------------------------------+
| event            | Debug LDP events                                |
+------------------+-------------------------------------------------+
| fsm              | Debug LDP finite state machine                  |
+------------------+-------------------------------------------------+
| igp-sync         | Debug LDP IGP sync (for both targeted sessions) |
+------------------+-------------------------------------------------+
| packet           | Debug LDP packets                               |
+------------------+-------------------------------------------------+
| rib              | Debug LDP RIB                                   |
+------------------+-------------------------------------------------+
| graceful-restart | Debug LDP graceful-restart recovery             |
+------------------+-------------------------------------------------+
| neighbor         | Debug LDP neighbor events                       |
+------------------+-------------------------------------------------+
| adjacency        | Debug LDP adjacency events                      |
+------------------+-------------------------------------------------+
| operational-db   | Debug LDP connection with oper-db               |
+------------------+-------------------------------------------------+
| message          | Debug LDP neighbor messages                     |
+------------------+-------------------------------------------------+
| l2vpn            | Debug LDP l2vpn and pw events                   |
+------------------+-------------------------------------------------+
| nsr              | enable ldp nsr main events logging              |
+------------------+-------------------------------------------------+
| trius            | Debug output related to interception of TCP     |
|                  | packets                                         |
+------------------+-------------------------------------------------+
| nsrdb            | Debug output for NSR DB                         |
+------------------+-------------------------------------------------+
| full-sync        | Debug output for ldp nsr synchronization        |
|                  | state with standby                              |
+------------------+-------------------------------------------------+
| rlfa             | Debug remote lfa LDP support                    |
+------------------+-------------------------------------------------+
| multipoint       | Debug mLDP                                      |
+------------------+-------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# ldp bindings
	dnRouter(cfg-debug)# ldp event
	dnRouter(cfg-debug)# ldp fsm
	dnRouter(cfg-debug)# ldp igp-sync
	dnRouter(cfg-debug)# ldp packet
	dnRouter(cfg-debug)# ldp rib
	dnRouter(cfg-debug)# ldp


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no ldp event
	dnRouter(cfg-debug)# no ldp fsm
	dnRouter(cfg-debug)# no ldp igp-sync


.. **Help line:** Debug LDP events

**Command History**

+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                                    |
+=========+=================================================================================================================================================+
| 6.0     | Command introduced                                                                                                                              |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 7.0     | Updated the non-persistent debug logging command to a "set" command                                                                             |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Replaced "no set" with unset                                                                                                                    |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 11.5    | Applied new debug hierarchy                                                                                                                     |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 15.0    | Added support for new debug parameters - graceful restart recovery, neighbor events, adjacency events, oper-db connection and neighbor messages |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for new debug parameter - 12vpn and pw events                                                                                     |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Added support for new debug parameter - nsr, trius, nsrdb, full-sync                                                                            |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Added support for new debug parameter - multipoint (mLDP)                                                                                       |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| 16.2    | Removed set-debug command                                                                                                                       |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------+