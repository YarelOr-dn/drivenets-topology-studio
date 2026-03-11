debug arp
----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug RIB ARP/NDP events:

**Command syntax: arp**
**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- The debug information is written in the rib-manager log file.
- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# arp


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no arp


.. **Help line:** Debug RIB ARP/NDP events

**Command History**

+---------+----------------------------------------------------------------------+
| Release | Modification                                                         |
+=========+======================================================================+
| 6.0     | Command introduced                                                   |
+---------+----------------------------------------------------------------------+
| 7.0     | Updated the non-persistent debug logging command to a "set" command. |
+---------+----------------------------------------------------------------------+
| 11.5    | Applied new debug hierarchy                                          |
+---------+----------------------------------------------------------------------+
| 16.2    | Removed set-debug command                                            |
+---------+----------------------------------------------------------------------+