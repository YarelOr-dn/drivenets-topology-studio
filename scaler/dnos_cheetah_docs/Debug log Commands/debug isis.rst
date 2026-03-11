debug isis
-----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug IS-IS events:

**Command syntax: isis** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all isis events will be debugged.

- Each command can be negated using the no or unset command prefix.

- The debug information is written in the isisd log file.

-  When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

**Parameter table**

+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| Argument                    | Description                                                                                                  |
+=============================+==============================================================================================================+
| adj-packets                 | IS-IS adjacency-related packets, such as hello packets sent and IS-IS received adjacencies going up and down |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| bfd                         | Debug BFD for IS-IS events                                                                                   |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| bgp-ls                      | Debug distribute link-state information to BGP                                                               |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| checksum-errors             | IS-IS LSP checksum errors                                                                                    |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| cspf                        | Debug ted CSPF                                                                                               |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| cspf-detailed               | Debug detailed ted CSPF                                                                                      |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| events                      | IS-IS events                                                                                                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| graceful-restart            | IS-IS graceful restart event                                                                                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| local-updates               | IS-IS local update related packets                                                                           |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| lsp-gen                     | IS-IS generation of own LSPs                                                                                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| lsp-sched                   | IS-IS scheduling of LSP generation                                                                           |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| packet-dump                 | IS-IS packet dump                                                                                            |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| protocol-errors             | IS-IS LSP protocol errors                                                                                    |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| rib                         | RIB manager debug information                                                                                |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| route-events                | IS-IS Route related events                                                                                   |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| snp-packets                 | IS-IS CSNP/PSNP packets                                                                                      |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| spf-events                  | IS-IS Shortest Path First Events                                                                             |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| spf-lfa                     | Debug IS-IS events related to loop-free-alternate routes                                                     |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| spf-statistics              | IS-IS SPF Timing and Statistic Data                                                                          |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| spf-triggers                | IS-IS SPF triggering events                                                                                  |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| sr                          | Debug segment-routing events                                                                                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| update-packets              | IS-IS Update related packets                                                                                 |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| aggregate-route-events      | Debug aggregate-route operations                                                                             |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| ti-lfa                      | Debug main events in isis sr ti-lfa logic                                                                    |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| ti-lfa-detail               | Debug all events in isis sr ti-lfa logic                                                                     |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| microloop-avoidance         | Debug main events in isis sr microloop-avoidance logic                                                       |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| microloop-avoidance-detail  | Debug all events in isis sr microloop-avoidance logic                                                        |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| rlfa                        | Debug events in isis remote lfa logic                                                                        |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+
| rlfa-detaiil                | Debug all events in isis remote lfa logic                                                                    |
+-----------------------------+--------------------------------------------------------------------------------------------------------------+

microloop-avoidance-detail

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# isis adj-packets
	dnRouter(cfg-debug)# isis checksum-errors
	dnRouter(cfg-debug)# isis events
	dnRouter(cfg-debug)# isis local-updates
	dnRouter(cfg-debug)# isis lsp-gen
	dnRouter(cfg-debug)# isis lsp-sched
	dnRouter(cfg-debug)# isis packet-dump
	dnRouter(cfg-debug)# isis protocol-errors
	dnRouter(cfg-debug)# isis route-events
	dnRouter(cfg-debug)# isis snp-packets
	dnRouter(cfg-debug)# isis spf-events
	dnRouter(cfg-debug)# isis spf-statistics
	dnRouter(cfg-debug)# isis spf-triggers
	dnRouter(cfg-debug)# isis update-packets
	dnRouter(cfg-debug)# isis aggregate-route-events
	dnRouter(cfg-debug)# isis bfd
	dnRouter(cfg-debug)# isis


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no isis lsp-gen
	dnRouter(cfg-debug)# no isis lsp-sched
	dnRouter(cfg-debug)# no isis protocol-errors
	dnRouter(cfg-debug)# no isis snp-packets
	dnRouter(cfg-debug)# no isis bfd

.. **Help line:** Debug IS-IS events

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 6.0     | Command introduced                        |
+---------+-------------------------------------------+
| 9.0     | Added debug graceful restart event        |
+---------+-------------------------------------------+
| 11.5    | Applied new debug hierarchy               |
+---------+-------------------------------------------+
| 12.0    | Added support for BFD for IS-IS           |
+---------+-------------------------------------------+
| 13.0    | Added the spf-lfa debug parameter         |
+---------+-------------------------------------------+
| 14.0    | Added the segment-routing debug parameter |
+---------+-------------------------------------------+
| 15.1    | Added aggregate-route-events parameter    |
+---------+-------------------------------------------+
| 16.2    | Added new ti-lfa debug parameters         |
+---------+-------------------------------------------+
| 16.2    | Removed set-debug command                 |
+---------+-------------------------------------------+