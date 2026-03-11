show dnos-internal ncp bfd
--------------------------

**Minimum user role:** viewer

To display NCP internal information for the BFD protocol:

**Command syntax:show dnos-internal ncp [ncp-id] bfd {stats | config | sessions-db | sessions | frr-events | period-profiles | txrx-profiles}**

**Command mode:** operation

**Parameter table**

+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| Parameter          | Description                                                           | Range                      |
+====================+=======================================================================+============================+
|                    |                                                                       |                            |
| ncp-id             | Filters the output to information on the specified NCP only           | 0..cluster type maximum -1 |
|                    |                                                                       |                            |
|                    |                                                                       | \* all NCPs                |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| stats              | Displays information on BFD statistics                                | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| config             | Displays configuration information                                    | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| session-db         | Displays DNOS internal information on configured sessions database    | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| sessions           | Displays information on configured sessions                           | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| frr-events         | Displays information on fast reroute events triggered by BFD          | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| period-profiles    | Displays period profiles that are currently used by the NPU           | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+
|                    |                                                                       |                            |
| txrx-profiles      | Displays txrx profiles that are currently used by the NPU             | \-                         |
+--------------------+-----------------------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter# # show dnos-internal ncp * bfd stats

	NCP 2 Table: /ubfd/stats
	dropped_packets:                           5
	dropped_packets_unknown_interface:         0
	dropped_packets_non_configured_interface:  0
	dropped_packets_parser_error:              0
	dropped_packets_standby_session:           0
	dropped_packets_invalid_state:             0
	dropped_packets_no_matching_session:       0
	dropped_packets_invalid_port:              0
	dropped_packets_rdisc_change:              0
	wrong_packets:                             0
	invalid_your_discriminator:                0
	...


	dnRouter# show dnos-internal ncp * bfd config

	NCP 2 Table: /bfd/config
	dscp:  48

	NCP 0 Table: /bfd/config
	dscp:  48

	NCP 3 Table: /bfd/config
	dscp:  48

	NCP 1 Table: /bfd/config
	dscp:  48


	dnRouter# show dnos-internal ncp * bfd frr-events

	NCP 2 Table: /bfd/frr_events

	| event_time          | type       | clients   | local_discriminator   | remote_discriminator   |
	|---------------------+------------+-----------+-----------------------+------------------------|
	| 2020-01-12 09:38:47 | RSVP Head  | RSVP_MPLS | 16048                 | 16960                  |
	| 2020-01-12 09:38:47 | RSVP Head  | RSVP_MPLS | 16964                 | 17008                  |
	| 2020-01-12 09:38:47 | RSVP Head  | RSVP_MPLS | 16052                 | 16964                  |
	| 2020-01-12 09:38:47 | RSVP Head  | RSVP_MPLS | 16968                 | 17012                  |
	| 2020-01-12 09:38:48 | RSVP Head  | RSVP_MPLS | 19572                 | 16160                  |
	| 2020-01-12 09:38:48 | RSVP Head  | RSVP_MPLS | 16076                 | 16008                  |
	| 2020-01-12 09:38:48 | RSVP Head  | RSVP_MPLS | 17400                 | 16112                  |
	| 2020-01-12 09:38:48 | RSVP Head  | RSVP_MPLS | 17396                 | 16116                  |
	| 2020-01-12 09:46:16 | RSVP Head  | RSVP_MPLS | 25228                 | 18688                  |
	| 2020-01-12 09:46:16 | RSVP Head  | RSVP_MPLS | 23932                 | 18408                  |


	dnRouter# show dnos-internal ncp * bfd sessions

	NCP 2 Table: /bfd/sessions_summary

	| l_disc   | r_disc   | state      | type       | interface                               | local_address                           | neighbor_address                        |
	|----------+----------+------------+------------+-----------------------------------------+-----------------------------------------+-----------------------------------------|
	| 324      | 4        | UP         | uBFD       | ge100-2/0/0                             | 101.0.0.19                              | 101.0.0.17                              |
	| 404      | 412      | UP         | uBFD       | ge100-2/0/20                            | 2001:0101:0000:0000:0000:0000:0000:0019 | 2001:0100:0000:0000:0000:0000:0000:0002 |
	| 408      | 416      | UP         | uBFD       | ge100-2/0/21                            | 2001:0101:0000:0000:0000:0000:0000:0019 | 2001:0100:0000:0000:0000:0000:0000:0002 |
	| 412      | 420      | UP         | uBFD       | ge100-2/0/22                            | 2001:0101:0000:0000:0000:0000:0000:0019 | 2001:0100:0000:0000:0000:0000:0000:0002 |
	| 416      | 424      | UP         | uBFD       | ge100-2/0/23                            | 2001:0101:0000:0000:0000:0000:0000:0019 | 2001:0100:0000:0000:0000:0000:0000:0002 |
	| 420      | 428      | UP         | uBFD       | ge100-2/0/24                            | 2001:0101:0000:0000:0000:0000:0000:0019 | 2001:0100:0000:0000:0000:0000:0000:0002 |
	...


	dnRouter# show dnos-internal ncp * bfd sessions-db

	NCP 2 Table: /bfd/sessions_db
	ubfd_max_sessions:           45
	bfd_max_sessions:          2048
	total_bfd_sessions_count:  2093
	n_neighbor_hm_entries:        1
	n_ldisc_hm_entries:          46
	n_rsvp_tail_hm_entries:      16
	n_port_id_entries:           15
	n_sh_sessions:                1
	n_mh_sessions:                0
	m_rsvp_head_sessions:        14
	list_count:                  46

	NCP 0 Table: /bfd/sessions_db
	ubfd_max_sessions:           45
	bfd_max_sessions:          2048
	total_bfd_sessions_count:  2093
	...


	dnRouter# show dnos-internal ncp * bfd period-profiles

	NCP 2 Table: /bfd/period_profiles

	| index   | refcount   | bfd_period   | is_bfd   |
	|---------+------------+--------------+----------|
	| 0       | 1          | 0            | 1        |
	| 1       | 1          | 50000        | 1        |
	| 2       | 15         | 50000        | 0        |
	| 3       | 30         | 100000       | 1        |
	NCP 0 Table: /bfd/period_profiles

	| index   | refcount   | bfd_period   | is_bfd   |
	|---------+------------+--------------+----------|
	| 0       | 2          | 0            | 1        |
	| 1       | 1          | 50000        | 1        |
	| 3       | 30         | 100000       | 1        |
	...


	dnRouter# show dnos-internal ncp * bfd txrx-profiles

	NCP 2 Table: /bfd/txrx_profiles

	| index   | refcount   | des_min_tx   | req_min_rx   |
	|---------+------------+--------------+--------------|
	| 0       | 1          | 1000000      | 1000000      |
	| 1       | 31         | 50000        | 50000        |
	| 2       | 8          | 100000       | 100000       |
	NCP 0 Table: /bfd/txrx_profiles

	| index   | refcount   | des_min_tx   | req_min_rx   |
	|---------+------------+--------------+--------------|
	| 0       | 2          | 1000000      | 1000000      |
	| 1       | 16         | 50000        | 50000        |
	| 2       | 8          | 100000       | 100000       |
	...

.. **Help line:** Displays NCP internal information regarding bfd protocol

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+
