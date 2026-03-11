show dnos-internal routing fib-manager fpm stats
------------------------------------------------

**Minimum user role:** viewer

To display fib-manager forwarding data distribution information:

**Command syntax: show dnos-internal routing fib-manager fpm stats {ncp [ncp-id] \| rib-manager \| summary}**

**Command mode:** operation

**Parameter table**

+----------------+-------------------------------------------------------------+
|                |                                                             |
| Parameter      | Description                                                 |
+================+=============================================================+
|                |                                                             |
| ncp-id         | Displays information installed in the specified NCP only    |
+----------------+-------------------------------------------------------------+
|                |                                                             |
| rib-manager    | Displays information received from the RIB                  |
+----------------+-------------------------------------------------------------+
|                |                                                             |
| summary        | Displays summary information                                |
+----------------+-------------------------------------------------------------+

**Example**
::

	
	dnRouter# show dnos-internal routing fib-manager fpm stats ncp 1
	NCP ID 1 (1), Name: ncp1_1900689510
	Connection state: UP, uptime: 4d22h26m
	Connection namespace: /proc/1/ns/net
	NSF:
	 EoR: sent
	
	Counter                                                 Total     Last 10 secs
	
	Connection Stats:
	---------------
	connect_calls                                               0                0
	write_cb_calls                                           5273                0
	max_writes_hit                                              2                0
	t_write_yields                                              8                0
	write_error_full_queue                                      0                0
	nsf_stale_timer_sets                                        2                0
	eor_marker_messages                                         2                0
	t_conn_down_starts                                          0                0
	t_conn_down_route_processed                                 0                0
	t_conn_down_ack_egress_processed                            0                0
	t_conn_down_neighbor_processed                              0                0
	t_conn_down_yields                                          0                0
	t_conn_down_finishes                                        0                0
	t_conn_up_starts                                            1                0
	t_conn_up_route_processed                                  10                0
	t_conn_up_neighbor_processed                                1                0
	t_conn_up_yields                                            0                0
	t_conn_up_aborts                                            0                0
	t_conn_up_finishes                                          1                0
	
	RX Stats:
	---------------
	neighbor_request_new                                        1                0
	neighbor_request_update                                     0                0
	mc_event_nocache_new                                        0                0
	mc_event_nocache_update                                     0                0
	mc_event_wrongif_new                                        0                0
	mc_event_wrongif_update                                     0                0
	mc_event_wholepacket_new                                    0                0
	mc_event_wholepacket_update                                 0                0
	mc_event_unknown                                            0                0
	egress_request_new                                          0                0
	egress_request_update                                     894                0
	egress_withdraw                                             0                0
	egress_withdraw_not_found                                   0                0
	egress_ack                                               1858                0
	egress_ack_not_found                                        0                0
	
	TX Stats:
	---------------
	routes low delete   nop_deletes_skipped                     0                0
	routes low delete   adds                                    0                0
	routes low delete   dels                                    0                0
	routes low delete   updates_triggered                       0                0
	routes low delete   redundant_triggers                      0                0
	routes low delete   dests_del_after_update                  0                0
	routes low delete   updates_triggered_canceled              0                0
	routes med delete   nop_deletes_skipped                     0                0
	routes med delete   adds                                    0                0
	routes med delete   dels                                    0                0
	routes med delete   updates_triggered                       0                0
	routes med delete   redundant_triggers                      0                0
	routes med delete   dests_del_after_update                  0                0
	routes med delete   updates_triggered_canceled              0                0
	routes high delete  nop_deletes_skipped                     0                0
	routes high delete  adds                                    0                0
	routes high delete  dels                                    0                0
	routes high delete  updates_triggered                       0                0
	routes high delete  redundant_triggers                      0                0
	routes high delete  dests_del_after_update                  0                0
	routes high delete  updates_triggered_canceled              0                0
	egress delete       nop_deletes_skipped                     0                0
	egress delete       adds                                    0                0
	egress delete       dels                                    0                0
	egress delete       updates_triggered                       0                0
	egress delete       redundant_triggers                      0                0
	egress delete       dests_del_after_update                  0                0
	egress delete       updates_triggered_canceled              0                0
	nexthop delete      nop_deletes_skipped                     0                0
	nexthop delete      adds                                    0                0
	nexthop delete      dels                                    0                0
	nexthop delete      updates_triggered                       0                0
	nexthop delete      redundant_triggers                      0                0
	nexthop delete      dests_del_after_update                  0                0
	nexthop delete      updates_triggered_canceled              0                0
	tunnel delete       nop_deletes_skipped                     0                0
	tunnel delete       adds                                    0                0
	tunnel delete       dels                                    0                0
	tunnel delete       updates_triggered                       0                0
	tunnel delete       redundant_triggers                      0                0
	tunnel delete       dests_del_after_update                  0                0
	tunnel delete       updates_triggered_canceled              0                0
	neighbors           nop_deletes_skipped                     0                0
	neighbors           adds                                  893                0
	neighbors           dels                                    0                0
	neighbors           updates_triggered                     893                0
	neighbors           redundant_triggers                      0                0
	neighbors           dests_del_after_update                  0                0
	neighbors           updates_triggered_canceled              0                0
	tunnel add          nop_deletes_skipped                     0                0
	tunnel add          adds                                    1                0
	tunnel add          dels                                    0                0
	tunnel add          updates_triggered                       1                0
	tunnel add          redundant_triggers                      0                0
	tunnel add          dests_del_after_update                  0                0
	tunnel add          updates_triggered_canceled              0                0
	nexthop add         nop_deletes_skipped                     0                0
	nexthop add         adds                                    7                0
	nexthop add         dels                                    0                0
	nexthop add         updates_triggered                       7                0
	nexthop add         redundant_triggers                      0                0
	nexthop add         dests_del_after_update                  0                0
	nexthop add         updates_triggered_canceled              0                0
	egress add          nop_deletes_skipped                     0                0
	egress add          adds                                 1858                0
	egress add          dels                                    0                0
	egress add          updates_triggered                    1858                0
	egress add          redundant_triggers                   2606                0
	egress add          dests_del_after_update                  0                0
	egress add          updates_triggered_canceled              0                0
	egress acks         nop_deletes_skipped                     0                0
	egress acks         adds                                 3314                0
	egress acks         dels                                    0                0
	egress acks         updates_triggered                    3314                0
	egress acks         redundant_triggers                   5968                0
	egress acks         dests_del_after_update                  0                0
	egress acks         updates_triggered_canceled              0                0
	routes high add     nop_deletes_skipped                     0                0
	routes high add     adds                                   10                0
	routes high add     dels                                    0                0
	routes high add     updates_triggered                      10                0
	routes high add     redundant_triggers                      0                0
	routes high add     dests_del_after_update                  0                0
	routes high add     updates_triggered_canceled              0                0
	routes med add      nop_deletes_skipped                     0                0
	routes med add      adds                                    0                0
	routes med add      dels                                    0                0
	routes med add      updates_triggered                       0                0
	routes med add      redundant_triggers                      0                0
	routes med add      dests_del_after_update                  0                0
	routes med add      updates_triggered_canceled              0                0
	routes low add      nop_deletes_skipped                     0                0
	routes low add      adds                                    0                0
	routes low add      dels                                    0                0
	routes low add      updates_triggered                       0                0
	routes low add      redundant_triggers                      0                0
	routes low add      dests_del_after_update                  0                0
	routes low add      updates_triggered_canceled              0                0
	
	dnRouter# show dnos-internal routing fib-manager fpm stats rib-manager
	RIB-Manager
	Connection state: UP, uptime: 1d22h6m
	Connection namespace: /proc/1/ns/net
	NSF:
	
	Counter                                            Total     Last 10 secs
	
	Connection Stats:
	---------------
	connect_calls                                          0                0
	write_cb_calls                                         4                0
	max_writes_hit                                         0                0
	t_write_yields                                         0                0
	write_error_full_queue                                 0                0
	nsf_stale_timer_sets                                   0                0
	eor_marker_messages                                    0                0
	t_conn_down_starts                                     1                0
	t_conn_down_route_processed                           10                0
	t_conn_down_ack_egress_processed                       0                0
	t_conn_down_neighbor_processed                         1                0
	t_conn_down_yields                                     0                0
	t_conn_down_finishes                                   1                0
	t_conn_up_starts                                       2                0
	t_conn_up_route_processed                              0                0
	t_conn_up_neighbor_processed                           0                0
	t_conn_up_yields                                       0                0
	t_conn_up_aborts                                       0                0
	t_conn_up_finishes                                     2                0
	
	RX Stats:
	---------------
	add_route_new                                         10                0
	add_route_update                                       0                0
	add_route_same                                        11                0
	del_route                                              0                0
	add_mc_route_new                                       0                0
	add_mc_route_update                                    0                0
	add_mc_route_same                                      0                0
	del_mc_route                                           0                0
	add_nexthop_new                                        7                0
	add_nexthop_update                                     1                0
	add_nexthop_same                                       7                0
	del_nexthop                                            0                0
	add_tunnel_new                                         1                0
	add_tunnel_update                                      0                0
	add_tunnel_same                                        1                0
	del_tunnel                                             0                0
	add_neighbor_new                                       1                0
	add_neighbor_update                                  895                0
	add_neighbor_same                                    238                0
	last_update                                            0                0
	nsf_stale_timer_sets                                   2                0
	eor_marker_messages                                    2                0
	
	TX Stats:
	---------------
	neighbor req   nop_deletes_skipped                     0                0
	neighbor req   adds                                    4                0
	neighbor req   dels                                    0                0
	neighbor req   updates_triggered                       4                0
	neighbor req   redundant_triggers                      2                0
	neighbor req   dests_del_after_update                  4                0
	neighbor req   updates_triggered_canceled              0                0
	mc event       nop_deletes_skipped                     0                0
	mc event       adds                                    0                0
	mc event       dels                                    0                0
	mc event       updates_triggered                       0                0
	mc event       redundant_triggers                      0                0
	mc event       dests_del_after_update                  0                0
	mc event       updates_triggered_canceled              0                0
	
	
	dnRouter# show dnos-internal routing fib-manager fpm stats summary
	rib             (RIB-Manager), state: UP, uptime: 2m30s
	
	ncp2(0)         (ncp2_784270501), state: UP, uptime: 2m30s
	ncp1(1)         (ncp1_1900689510), state: UP, uptime: 1m27s
	ncp4(2)         (ncp4_2846399778), state: UP, uptime: 2m30s
	ncp3(3)         (ncp3_3962818787), state: UP, uptime: 2m30s
	ncp5(4)         (ncp5_1729980769), state: UP, uptime: 2m30s
	

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+


