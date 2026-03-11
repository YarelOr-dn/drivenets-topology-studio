show rib-manager fpm statistics
-------------------------------

**Minimum user role:** viewer

To display routing statistics related to the forwarding elements:



**Command syntax: show rib-manager fpm statistics**

**Command mode:** operational




**Example**
::

	dnRouter# show rib-manager fpm statistics
	Cheetah ID 1 URI tcp://10.253.0.10:8877
	Connection state: UP
	Connection namespace: /proc/1/ns/net
	NSF:
	 NSF start state: normal
	 EoR: sent
	
	Counter                                       Total     Last 10 secs
	
	connect_calls                                     1                0
	connect_no_sock                                   0                0
	read_cb_calls                                     0                0
	write_cb_calls                           1188390433                0
	write_calls                                       0                0
	max_writes_hit                             10741019                0
	t_write_yields                               255517                0
	write_error_full_queue                   1084285482                0
	t_conn_down_starts                               95                0
	t_conn_down_dests_processed                 9709595                0
	t_conn_down_yields                             2366                0
	t_conn_down_finishes                            190                0
	t_conn_up_starts                                 96                0
	t_conn_up_dests_processed                   3396393                0
	t_conn_up_yields                                523                0
	t_conn_up_aborts                                  0                0
	t_conn_up_finishes                              192                0
	neighbors nop_deletes_skipped                     0                0
	neighbors adds                                 2361                0
	neighbors dels                                    0                0
	neighbors updates_triggered                    2373                0
	neighbors redundant_triggers                     25                0
	neighbors non_fpm_table_triggers                  0                0
	neighbors dests_del_after_update                  0                0
	routes    nop_deletes_skipped               3073657                0
	routes    adds                            113847577                0
	routes    dels                             87440534                0
	routes    updates_triggered               212460084                0
	routes    redundant_triggers               12257975                0
	routes    non_fpm_table_triggers                  0                0
	routes    dests_del_after_update           90417547                0
	routes    nsf_stale_timer_sets                  165                0
	routes    eor_marker_messages                    90                0
	
	

.. **Help line:** Routing statistics related to the Forwarding elements

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+

