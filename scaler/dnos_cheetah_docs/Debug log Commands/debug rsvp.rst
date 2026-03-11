debug rsvp
-----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug RSVP events:

**Command syntax: rsvp** [parameter]


**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all rsvp events will be debugged.

- Each command can be negated using the no or unset command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the rsvpd log file.

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Argument          | Description                                                                                                                                                                         |
+===================+=====================================================================================================================================================================================+
| auto-bandwidth    | logs auto-bandwidth related activity (e.g. counters update, adjust/overflow/underflow events, and related CLI changes)                                                              |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| auto-mesh         | logs auto-mesh related activity (e.g. creation/update/deletion of auto-mesh tunnels, updates from IGP, matching info, peer info)                                                    |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| backup            | logs FRR activity (mainly creation and deletion of auto-bypass and backup tunnels)                                                                                                  |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| cac               | logs control admission activity (e.g. allocation/deallocation of bandwidth per interface/tunnel, preemption tunnels, TE parameters update)                                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| cli               | logs all configuration/show related activity (e.g. any configuration change, any show performed with details on filtered tunnels)                                                   |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| events            | logs significant RSVP events                                                                                                                                                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| frr               | logs fast reroute activity (e.g. tunnel's requests for protection, protection matching, periodic matching)                                                                          |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| lsp               | logs LSP lifetime activity (e.g. all LSP events, creation/update/deletion of LSPs, any change related to the LSP)                                                                   |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| nsf               | log non-stop forwarding activity (e.g. data checkpointing, restore operation activity)                                                                                              |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| optimization      | logs optimization related activity (e.g. optimization candidates selection, optimization state machine, optimization decisions, LSP notifications regarding optimization decisions) |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| packets           | logs RSVP packets activity (e.g. sent/received packets)                                                                                                                             |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| pcep              | logs PCE activity (e.g. connectivity manager, updates to/from the PCE)                                                                                                              |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| refresh-reduction | logs reduction activity (e.g. sending/receiving/building SR/bundle messages)                                                                                                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| rib-manager       | logs RIB manager activity (e.g. installed/uninstalled tunnels, received/sent messages to/from the RIB manager)                                                                      |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| states            | logs tunnel/group/LSP state changes activity                                                                                                                                        |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| timers            | logs RSVP timers set/expire activity                                                                                                                                                |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# rsvp
	dnRouter(cfg-debug)# rsvp cac
	dnRouter(cfg-debug)# rsvp events
	dnRouter(cfg-debug)# rsvp lsp
	dnRouter(cfg-debug)# rsvp packets
	dnRouter(cfg-debug)# rsvp states
	dnRouter(cfg-debug)# rsvp timers
	dnRouter(cfg-debug)# rsvp rib-manager
	dnRouter(cfg-debug)# rsvp pcep
	dnRouter(cfg-debug)# rsvp backup
	dnRouter(cfg-debug)# rsvp frr
	dnRouter(cfg-debug)# rsvp cli
	dnRouter(cfg-debug)# rsvp nsf
	dnRouter(cfg-debug)# rsvp auto-mesh
	dnRouter(cfg-debug)# rsvp auto-bw
	dnRouter(cfg-debug)# rsvp refresh-reduction
	dnRouter(cfg-debug)# rsvp optimization

	dnRouter(cfg-debug)# rsvp timers
	dnRouter(cfg-debug)# rsvp

**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no rsvp frr

.. **Help line:**

**Command History**

+---------+-------------------------------------------------------------------------------------+
| Release | Modification                                                                        |
+=========+=====================================================================================+
| 9.0     | Command introduced                                                                  |
+---------+-------------------------------------------------------------------------------------+
| 11.0    | Added support for debugging auto-bw, auto-mesh, thresholds, optimization, and SNMP. |
+---------+-------------------------------------------------------------------------------------+
| 11.5    | Applied new debug hierarchy                                                         |
+---------+-------------------------------------------------------------------------------------+
| 16.2    | Removed set-debug command                                                           |
+---------+-------------------------------------------------------------------------------------+