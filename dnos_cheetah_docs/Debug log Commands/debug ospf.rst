debug ospf
-----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug OSPF events:

**Command syntax: ospf** [parameter]
**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all ospf events will be debugged.

- Each command can be negated using the no or unset command prefix.

- ism status, events, timer can be set together. Use "debug ospf ism" to set all three.

- lsa generate, flooding, install, refresh can be set together. Use "debug ospf lsa" to set all four.

- nsm status, events, timer can be set together. Use "debug ospf nsm" to set all three.

- packet  with no optional parameters is used for debugging all ospf packet options. Alternatively, specify one (or more) options from the different packet types. Use "send" or "recv" to specify a packet direction, otherwise debug logging will be carried out for both send and receive. Use "detail" detailed debug information.

- You can set either rib interface or redistribute. Use "debug ospf rib" to set both.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

-  When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the ospfd log file.


**Parameter table**

+------------------------------------------------------------------------+---------------------------------------------------+
| Argument                                                               | Description                                       |
+========================================================================+===================================================+
| **event**                                                              | Debug information of OSPF event                   |
+------------------------------------------------------------------------+---------------------------------------------------+
| **event-gr**                                                           | Debug information of OSPF graceful restart event  |
+------------------------------------------------------------------------+---------------------------------------------------+
| **packet (hello|dd|ls-request|ls-update|ls-ack)** (send|recv) [detail] | Dump packets for debugging                        |
+------------------------------------------------------------------------+---------------------------------------------------+
| **ism** (status, events, timers)                                       | Debug information of OSPF Interface State Machine |
+------------------------------------------------------------------------+---------------------------------------------------+
| **nsm** (status, events, timers)                                       | Debug information of OSPF Network State Machine   |
+------------------------------------------------------------------------+---------------------------------------------------+
| **lsa** (generate, flooding, refresh, install)                         | Debug detail of OSPF Link State messages          |
+------------------------------------------------------------------------+---------------------------------------------------+
| **nssa**                                                               | Debug information about Not So Stub Area          |
+------------------------------------------------------------------------+---------------------------------------------------+
| **spf** lfa                                                            | Debug information of SPF runs and calculations    |
+------------------------------------------------------------------------+---------------------------------------------------+
| **rib** {interface|redistribute}                                       | Debug information of RIB manager API              |
+------------------------------------------------------------------------+---------------------------------------------------+
| **cspf**                                                               | Debug information of constrained SPF              |
+------------------------------------------------------------------------+---------------------------------------------------+
| **mpls-te**                                                            | Debug information of OSPF Traffic Engineering     |
+------------------------------------------------------------------------+---------------------------------------------------+
| **ldp-sync**                                                           | Debug events related to igp-ldp sync in OSPF      |
+------------------------------------------------------------------------+---------------------------------------------------+
| **sr**                                                                 | Debug events related to segment-routing support   |
+------------------------------------------------------------------------+---------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug ospf event
	dnRouter(cfg)# debug ospf event-gr
	dnRouter(cfg)# debug ospf ism status
	dnRouter(cfg)# debug ospf ism events
	dnRouter(cfg)# debug ospf ism
	dnRouter(cfg)# debug ospf lsa generate
	dnRouter(cfg)# debug ospf lsa install
	dnRouter(cfg)# debug ospf lsa refresh
	dnRouter(cfg)# debug ospf lsa
	dnRouter(cfg)# debug ospf nsm status
	dnRouter(cfg)# debug ospf nsm events
	dnRouter(cfg)# debug ospf nsm
	dnRouter(cfg)# debug ospf nssa
	dnRouter(cfg)# debug ospf packet hello
	dnRouter(cfg)# debug ospf packet dd
	dnRouter(cfg)# debug ospf packet ls-update send
	dnRouter(cfg)# debug ospf packet ls-ack recv detail
	dnRouter(cfg)# debug ospf packet ls-request detail
	dnRouter(cfg)# debug ospf packet dd detail
	dnRouter(cfg)# debug ospf spf
	dnRouter(cfg)# debug ospf spf lfa
	dnRouter(cfg)# debug ospf rib interface
	dnRouter(cfg)# debug ospf rib redistribute
	dnRouter(cfg)# debug ospf rib
	dnRouter(cfg)# debug ospf bfd
	dnRouter(cfg)# debug ospf mpls-te
	dnRouter(cfg)# debug ospf cspf



**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg)# no debug ospf event-gr
	dnRouter(cfg)# no debug ospf event
	dnRouter(cfg)# no debug ospf ism events
	dnRouter(cfg)# no debug ospf lsa refresh
	dnRouter(cfg)# no debug ospf nsm events
	dnRouter(cfg)# no debug ospf nssa
	dnRouter(cfg)# no debug ospf packet ls-ack recv detail
	dnRouter(cfg)# no debug ospf packet detail
	dnRouter(cfg)# no debug ospf spf
	dnRouter(cfg)# no debug ospf rib redistribute
	dnRouter(cfg)# no debug ospf bfd
	dnRouter(cfg)# no debug ospf mpls-te
	dnRouter(cfg)# no debug ospf cspf


.. **Help line:** Debug OSPF events

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 11.6    | Command introduced                                |
+---------+---------------------------------------------------+
| 13.1    | Added support for cspf and mpls-te                |
+---------+---------------------------------------------------+
| 15.0    | Added support for IGP-LDP synchronization on OSPF |
+---------+---------------------------------------------------+
| 16.2    | Removed set-debug command                         |
+---------+---------------------------------------------------+