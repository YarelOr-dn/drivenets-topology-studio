debug ospfv3
------------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug OSPFv3 events:

**Command syntax: ospfv3** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, all ospfv3 events will be debugged.

- Each command can be negated using the no or unset command prefix.

- All lsa options can be set together.

- packet  with no optional parameters is used for debugging all ospf packet options. Alternatively, specify one (or more) options from the different packet types. Use "send" or "recv" to specify a packet direction, otherwise debug logging will be carried out for both send and receive. Use "detail" detailed debug information.

- You can set either rib interface or redistribute. Use "debug ospfv3 rib" to set both.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the ospfd log file.


**Parameter table**

+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| Argument                                                                                        | Description                                     |
+=================================================================================================+=================================================+
| **interface**                                                                                   | Debug information of Interface State Machine    |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **lsa (as-ext | inter-prefix | inter-router | intra-prefix | link)** {network | router | type7} | Debug detail of OSPFv3 Link State messages      |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **neighbor**                                                                                    | Debug information of neighbor                   |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **route**                                                                                       | Debug information about route table calculation |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **packet (hello|dd|ls-request|ls-update|ls-ack)** (send|recv) [detail]                          | Dump packets for debugging                      |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **spf**                                                                                         | Debug information of SPF runs and calculations  |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **rib** {interface|redistribute}                                                                | Debug information of RIB manager API            |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **bfd**                                                                                         | Debug OSPFv3 BFD events                         |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+
| **graceful-restart**                                                                            | Debug information of OSPFv3 Graceful Restart    |
+-------------------------------------------------------------------------------------------------+-------------------------------------------------+

**Example**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# debug ospfv3 interface

	dnRouter(cfg)# debug ospfv3 lsa as-ext
	dnRouter(cfg)# debug ospfv3 lsa inter-prefix
	dnRouter(cfg)# debug ospfv3 lsa inter-router
	dnRouter(cfg)# debug ospfv3 lsa intra-prefix
	dnRouter(cfg)# debug ospfv3 lsa link
	dnRouter(cfg)# debug ospfv3 lsa network
	dnRouter(cfg)# debug ospfv3 lsa router
	dnRouter(cfg)# debug ospfv3 lsa type7
	dnRouter(cfg)# debug ospfv3 lsa
	dnRouter(cfg)# debug ospfv3 neighbor
	dnRouter(cfg)# debug ospfv3 neighbor event
	dnRouter(cfg)# debug ospfv3 neighbor state
	dnRouter(cfg)# debug ospfv3 route
	dnRouter(cfg)# debug ospfv3 packet hello
	dnRouter(cfg)# debug ospfv3 packet dd
	dnRouter(cfg)# debug ospfv3 packet ls-update send
	dnRouter(cfg)# debug ospfv3 packet ls-ack recv
	dnRouter(cfg)# debug ospfv3 packet ls-request detail
	dnRouter(cfg)# debug ospfv3 packet dd detail
	dnRouter(cfg)# debug ospfv3 spf
	dnRouter(cfg)# debug ospfv3 rib interface
	dnRouter(cfg)# debug ospfv3 rib redistribute
	dnRouter(cfg)# debug ospfv3 rib
	dnRouter(cfg)# debug ospfv3 bfd
	dnRouter(cfg)# debug ospfv3 graceful-restart


**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg)# no debug ospfv3 lsa network
	dnRouter(cfg)# no debug ospfv3 neighbor
	dnRouter(cfg)# no debug ospfv3 route
	dnRouter(cfg)# no debug ospfv3 packet ls-ack detail
	dnRouter(cfg)# no debug ospfv3 packet detail
	dnRouter(cfg)# no debug ospfv3 spf
	dnRouter(cfg)# no debug ospfv3 rib redistribute
	dnRouter(cfg)# no debug ospfv3 bfd
	dnRouter(cfg)# no debug ospfv3 graceful-restart


.. **Help line:** Debug OSPFv3 events

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 11.6    | Command introduced                 |
+---------+------------------------------------+
| 13.1    | Added support for graceful-restart |
+---------+------------------------------------+
| 16.2    | Removed set-debug command          |
+---------+------------------------------------+