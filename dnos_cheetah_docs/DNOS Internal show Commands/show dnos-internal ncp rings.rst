show dnos-internal ncp rings
----------------------------

**Minimum user role:** viewer

To display statistics on rings that are used for IPC in wb-agent:

**Command syntax:show dnos-internal ncp [ncp-id] rings**

**Command mode:** operation

**Parameter table**

+---------------+-------------------------------------------------------+----------------------------+
|               |                                                       |                            |
| Parameter     | Description                                           | Range                      |
+===============+=======================================================+============================+
|               |                                                       |                            |
| ncp-id        | Display the information for the specified NCP only    | 0..cluster type maximum -1 |
|               |                                                       |                            |
|               |                                                       | \* all NCPs                |
+---------------+-------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter#  show dnos-internal ncp * rings

	NCP 0 Table: /rings

	| name                      | n_enqueues   | n_dequeues   | n_notification_errors   | n_full_queue_error   | n_enqueues-rate   | n_dequeues-rate   |
	|---------------------------+--------------+--------------+-------------------------+----------------------+-------------------+-------------------|
	| cfg_to_fib                | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| bfd_to_fib                | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| fib_to_bfd                | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| rx_to_bfd_ring            | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| oamp_to_bfd_ring          | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| conf_to_bfd_ring          | 1            | 1            | 0                       | 0                    | 0                 | 0                 |
	| cm_to_bfd_ring            | 1            | 1            | 0                       | 0                    | 0                 | 0                 |
	| bfd_mgr_to_db             | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| bfd_to_cnt                | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| oamp_conf_to_bfd          | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| bfd_to_oamp_conf          | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| bfd_to_oamp_conf_fast     | 1            | 1            | 0                       | 0                    | 0                 | 0                 |
	| em_critical_ring_0        | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| em_critical_ring_1        | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| em_critical_ring_2        | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| em_config_ring            | 82           | 82           | 0                       | 0                    | 0                 | 0                 |
	| pkt_tracer_queue          | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| ipfix_ret_sess_list       | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| cfg_event_ring            | 40           | 40           | 0                       | 0                    | 0                 | 0                 |
	| linkscan_event_ring       | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| cfg_mgr_to_db             | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| twamp deleted sessions    | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| lacp packets ring         | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| incoming pkts ring        | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| exported ipfix pkts ring  | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| fib processing info queue | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| em_comm_to_fib            | 1            | 1            | 0                       | 0                    | 0                 | 0                 |
	| lfs queue                 | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| hp_cnt_mgr_to_db_ring     | 15520        | 15520        | 0                       | 0                    | 0                 | 0                 |
	| dropped pkts ring         | 0            | 0            | 0                       | 0                    | 0                 | 0                 |
	| log_ring                  | 2222         | 2222         | 0                       | 0                    | 0                 | 0                 |
	...

.. **Help line:** Displays stats on rings that are used for IPC in wb-agent

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+
