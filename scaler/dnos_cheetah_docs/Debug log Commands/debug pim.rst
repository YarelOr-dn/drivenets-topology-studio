debug pim
-----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug PIM:

**Command syntax: pim** [parameter]
**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all pim events will be debugged.

- Each command can be negated using the no or unset command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the pimd log file.


**Parameter table**

+----------------------------------------------------+-------------------------------------------------+
| Parameter                                          | Description                                     |
+====================================================+=================================================+
| events                                             | PIM events debug information                    |
+----------------------------------------------------+-------------------------------------------------+
| {packets-hello | packets-join | packets-register}} | Logs Tx/Rx PIM packets with related information |
+----------------------------------------------------+-------------------------------------------------+
| errors                                             | Debug PIM protocol errors                       |
+----------------------------------------------------+-------------------------------------------------+
| mtrace                                             | Debug mtrace protocol                           |
+----------------------------------------------------+-------------------------------------------------+
| graceful-restart                                   | Debug PIM graceful-restart state-machine        |
+----------------------------------------------------+-------------------------------------------------+
| rib                                                | Debug the interface between PIM and RIB manager |
+----------------------------------------------------+-------------------------------------------------+
| trace                                              | PIM protocol traces                             |
+----------------------------------------------------+-------------------------------------------------+
| trace-detail                                       | PIM protocol detailed traces                    |
+----------------------------------------------------+-------------------------------------------------+

**Example**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# debug pim

	dnRouter(cfg)# debug pim events
	dnRouter(cfg)# debug pim mtrace
	dnRouter(cfg)# debug pim graceful-restart
	dnRouter(cfg)# debug pim rib



**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg)# no debug pim events
	dnRouter(cfg)# no debug pim packets-hello
	dnRouter(cfg)# no debug pim packets-join
	dnRouter(cfg)# no debug pim packets-register
	dnRouter(cfg)# no debug pim mtrace
	dnRouter(cfg)# no debug pim trace
	dnRouter(cfg)# no debug pim trace-detail
	dnRouter(cfg)# no debug pim graceful-restart
	dnRouter(cfg)# no debug pim rib


.. **Help line:** Debug PIM

**Command History**

+-------------+---------------------------+
|             |                           |
| Release     | Modification              |
+=============+===========================+
|             |                           |
| 12.0        | Command introduced        |
+-------------+---------------------------+
|             |                           |
| 16.2        | Removed set-debug command |
+-------------+---------------------------+