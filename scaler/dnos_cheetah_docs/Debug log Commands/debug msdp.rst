debug msdp
----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug MSDP:

**Command syntax: msdp** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all msdp events will be debugged.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the msdpd log file.

**Parameter table**

+-----------+--------------------------------------------------------------------------------+
| Parameter | Description                                                                    |
+===========+================================================================================+
| events    | Debug MSDP events including information about peer and sc-cache related events |
+-----------+--------------------------------------------------------------------------------+
| packets   | Debug sa-cache packets                                                         |
+-----------+--------------------------------------------------------------------------------+

**Example**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# debug msdp
	dnRouter(cfg)# debug msdp events
	dnRouter(cfg)# debug msdp packets

**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg)# no debug msdp events
	dnRouter(cfg)# no debug msdp packets
	dnRouter(cfg)# no debug msdp


.. **Help line:** Debug MSDP

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