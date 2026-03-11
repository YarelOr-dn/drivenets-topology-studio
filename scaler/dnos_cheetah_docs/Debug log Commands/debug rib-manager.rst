debug rib-manager
------------------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug RIB manager events:

**Command syntax: rib-manager** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all rib-manager events will be debugged.

- Each command can be negated using the no or unset command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.


**Parameter table**

+---------------------------+-------------------------------------------------------------------------------------------+
| Argument                  | Description                                                                               |
+===========================+===========================================================================================+
| events                    | Debug option set for RIB manager events                                                   |
+---------------------------+-------------------------------------------------------------------------------------------+
| fpm                       | Debug RIB manager FPM events                                                              |
+---------------------------+-------------------------------------------------------------------------------------------+
| kernel                    | Debug option set of rRIB manager between kernel interface                                 |
+---------------------------+-------------------------------------------------------------------------------------------+
| mpls                      | Debug option set for RIB manager MPLS LSPs                                                |
+---------------------------+-------------------------------------------------------------------------------------------+
| nht                       | Debug option set for RIB manager next hop tracking                                        |
+---------------------------+-------------------------------------------------------------------------------------------+
| rib                       | Debug RIB events                                                                          |
+---------------------------+-------------------------------------------------------------------------------------------+
| rib-queue                 | Debug RIB queuing                                                                         |
+---------------------------+-------------------------------------------------------------------------------------------+
| packet {recv|send} detail | Debug RIB manager packets                                                                 |
|                           | You can set either packet receive, packet send, or packet only for both receive and send. |
|                           | Add detail for detailed debugging information.                                            |
+---------------------------+-------------------------------------------------------------------------------------------+
| bfd                       | Enable bfd rib queue debug logging                                                        |
+---------------------------+-------------------------------------------------------------------------------------------+
| l2vpn                     | Enable l2vpn debug logging                                                                |
+---------------------------+-------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# rib-manager events
	dnRouter(cfg-debug)# rib-manager fpm
	dnRouter(cfg-debug)# rib-manager kernel
	dnRouter(cfg-debug)# rib-manager mpls
	dnRouter(cfg-debug)# rib-manager nht
	dnRouter(cfg-debug)# rib-manager rib
	dnRouter(cfg-debug)# rib-manager rib-queue
	dnRouter(cfg-debug)# rib-manager

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# rib-manager packet detail
	dnRouter(cfg-debug)# rib-manager packet recv detail
	dnRouter(cfg-debug)# rib-manager packet recv

**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no rib-manager fpm
	dnRouter(cfg-debug)# no rib-manager kernel
	dnRouter(cfg-debug)# no rib-manager mpls
	dnRouter(cfg-debug)# no rib-manager rib-queue

	dnRouter(cfg-debug)# no rib-manager packet send


.. **Help line:** Debug RIB manager events

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 6.0     | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 7.0     | Updated the non-persistent debug logging command to a "set" command |
+---------+---------------------------------------------------------------------+
| 11.4    | Added new BFD argument                                              |
+---------+---------------------------------------------------------------------+
| 11.5    | Applied new debug hierarchy                                         |
+---------+---------------------------------------------------------------------+
| 16.1    | Added support for new debug parameter - 12vpn and pw events         |
+---------+---------------------------------------------------------------------+
| 16.2    | Removed set-debug command                                           |
+---------+---------------------------------------------------------------------+