show dnos-internal operational
------------------------------

**Minimum user role:** viewer

**Description:**


**Command syntax:show dnos-internal operational ncc [ncc-id] {cpu | memory | keyspace | commandstats | stats | client info}**

**Command mode:** operation

**Parameter table**

+---------------+----------------------------------------------------------+------------------+-----------+
|               |                                                          |                  |           |
| Parameter     | Description                                              | Values           | Default   |
+===============+==========================================================+==================+===========+
|               |                                                          |                  |           |
| ncc-id        | Filter the displayed information to the specified NCC    | * - for all nccs | \-        |
|               |                                                          |                  |           |
|               |                                                          | 0..1             |           |
+---------------+----------------------------------------------------------+------------------+-----------+

The following information is displayed for the specified NCC:

- cpu - displays DNOS internal information on operational database CPU usage

- memory - displays DNOS internal information on operational database memory usage

- keyspace - displays DNOS internal information on operational database keyspace usage

- commandstats - displays DNOS internal information on operational database commands statistics

- stats - displays DNOS internal information on operational database general statistics

- clients info - displays db-client statistics and queue settings.


**Example**
::

	dev-dnRouter# show dnos-internal operational ncc 0 cpu

	NCC 0
	# CPU
	used_cpu_sys:8.278300
	used_cpu_user:7.999569
	used_cpu_sys_children:0.000000
	used_cpu_user_children:0.000000

	dev-dnRouter# show dnos-internal operational ncc 0 memory

	NCC 0
	# Memory
	used_memory:3241680
	used_memory_human:3.09M
	used_memory_rss:7794688
	used_memory_rss_human:7.43M
	used_memory_peak:3726848
	used_memory_peak_human:3.55M
	used_memory_peak_perc:86.98%
	used_memory_overhead:2550948
	used_memory_startup:792888
	used_memory_dataset:690732
	used_memory_dataset_perc:28.21%
	allocator_allocated:3337720
	allocator_active:4198400
	allocator_resident:9732096
	total_system_memory:135072284672
	total_system_memory_human:125.80G
	used_memory_lua:90112
	used_memory_lua_human:88.00K
	used_memory_scripts:26080
	used_memory_scripts_human:25.47K
	number_of_cached_scripts:12
	maxmemory:0
	maxmemory_human:0B
	maxmemory_policy:noeviction
	allocator_frag_ratio:1.26
	allocator_frag_bytes:860680
	allocator_rss_ratio:2.32
	allocator_rss_bytes:5533696
	rss_overhead_ratio:0.80
	rss_overhead_bytes:-1937408
	mem_fragmentation_ratio:2.44
	mem_fragmentation_bytes:4594024
	mem_not_counted_for_evict:0
	mem_replication_backlog:0
	mem_clients_slaves:0
	mem_clients_normal:1664564
	mem_aof_buffer:0
	mem_allocator:jemalloc-5.1.0
	active_defrag_running:0
	lazyfree_pending_objects:0

	dev-dnRouter# show dnos-internal operational ncc 0 keyspace

	NCC 0
	# Keyspace
	db0:keys=442,expires=175,avg_ttl=8353
	db1:keys=780,expires=0,avg_ttl=0

	dev-dnRouter# show dnos-internal operational ncc 0 commandstats

	NCC 0
	# Commandstats
	cmdstat_exists:calls=470,usec=1053,usec_per_call=2.24
	cmdstat_dn.uptime.hsetnx:calls=1,usec=13,usec_per_call=13.00
	cmdstat_script:calls=98,usec=2959,usec_per_call=30.19
	cmdstat_hset:calls=128121,usec=471510,usec_per_call=3.68
	cmdstat_dn.uptime.init:calls=2,usec=474,usec_per_call=237.00
	cmdstat_hvals:calls=5,usec=9,usec_per_call=1.80
	cmdstat_replicaof:calls=1,usec=173,usec_per_call=173.00
	cmdstat_set:calls=180320,usec=207698,usec_per_call=1.15
	cmdstat_scan:calls=3401,usec=459921,usec_per_call=135.23
	cmdstat_role:calls=2098,usec=11959,usec_per_call=5.70
	cmdstat_multi:calls=100471,usec=15436,usec_per_call=0.15
	cmdstat_get:calls=20430,usec=52573,usec_per_call=2.57
	cmdstat_hget:calls=937,usec=2186,usec_per_call=2.33
	cmdstat_del:calls=579,usec=1216,usec_per_call=2.10
	cmdstat_smembers:calls=27,usec=218,usec_per_call=8.07
	cmdstat_keys:calls=17,usec=447,usec_per_call=26.29
	cmdstat_incrby:calls=4061,usec=10815,usec_per_call=2.66
	cmdstat_ping:calls=4213,usec=3026,usec_per_call=0.72
	cmdstat_hgetall:calls=123948,usec=297619,usec_per_call=2.40
	cmdstat_select:calls=38,usec=48,usec_per_call=1.26
	cmdstat_mget:calls=8869,usec=35993,usec_per_call=4.06
	cmdstat_setex:calls=196,usec=982,usec_per_call=5.01
	cmdstat_dn.uptime.hset:calls=138,usec=4025,usec_per_call=29.17
	cmdstat_dn.uptime.hget:calls=841,usec=11538,usec_per_call=13.72
	cmdstat_evalsha:calls=1995,usec=545160,usec_per_call=273.26
	cmdstat_zadd:calls=83804,usec=81919,usec_per_call=0.98
	cmdstat_hdel:calls=169,usec=111,usec_per_call=0.66
	cmdstat_lpush:calls=43,usec=46,usec_per_call=1.07
	cmdstat_expire:calls=201953,usec=147197,usec_per_call=0.73
	cmdstat_hincrby:calls=100719,usec=108989,usec_per_call=1.08
	cmdstat_client:calls=38,usec=80,usec_per_call=2.11
	cmdstat_lrange:calls=138,usec=1216,usec_per_call=8.81
	cmdstat_exec:calls=100471,usec=836066,usec_per_call=8.32
	cmdstat_zrangebylex:calls=2964,usec=5862,usec_per_call=1.98
	cmdstat_hmset:calls=66,usec=154,usec_per_call=2.33
	cmdstat_zrank:calls=5698,usec=11372,usec_per_call=2.00
	cmdstat_sadd:calls=365,usec=1227,usec_per_call=3.36
	cmdstat_rpush:calls=37,usec=418,usec_per_call=11.30
	cmdstat_hsetnx:calls=1,usec=3,usec_per_call=3.00
	cmdstat_setnx:calls=2002,usec=1851,usec_per_call=0.92
	cmdstat_info:calls=11,usec=490,usec_per_call=44.55

	dev-dnRouter# show dnos-internal operational ncc 0 stats

	NCC 0
	# Stats
	total_connections_received:155
	total_commands_processed:1165035
	instantaneous_ops_per_sec:1599
	total_net_input_bytes:75933496
	total_net_output_bytes:29025655
	instantaneous_input_kbps:145.65
	instantaneous_output_kbps:70.83
	rejected_connections:0
	sync_full:0
	sync_partial_ok:0
	sync_partial_err:0
	expired_keys:0
	expired_stale_perc:0.00
	expired_time_cap_reached_count:0
	evicted_keys:0
	keyspace_hits:159346
	keyspace_misses:71795
	pubsub_channels:0
	pubsub_patterns:0
	latest_fork_usec:0
	migrate_cached_sockets:0
	slave_expires_tracked_keys:0
	active_defrag_hits:0
	active_defrag_misses:0
	active_defrag_key_hits:0
	active_defrag_key_misses:0


	dev-dnRouter# show dnos-internal operational clients info

	name                         hostname    container            keepalive        num        num          num          num              num      queue    queue
	                                         name                              command    command      objects      objects    reconnections       size     size
	                                                                              sent       sent    processed    processed                     current      max
	                                                                                         rate                      rate
	---------------------------  ----------  -----------------  -----------  ---------  ---------  -----------  -----------  ---------------  ---------  -------
	cli                          kgollan-pc  routing_engine               0         67          0           22            0                1          1        4
	cmc                          kgollan-pc  management-engine            1       4679          0         1506            0                4          0      161
	gnmi_agent                   kgollan-pc  routing_engine               2       3536          0         1178            0                1          1        4
	gnmi_server                  kgollan-pc  routing_engine               3       3561          0         1189            0                1          0        4
	isisd                        kgollan-pc  routing_engine               2       3552          0         1184            0                1          1        4
	pimd                         kgollan-pc  routing_engine               4       5907          1         2755            0                1          0        4
	process_monitor_probe        kgollan-pc  datapath1                    0      89720         28        22727            7                5          1       83
	process_monitor_probe        kgollan-pc  management-engine            2     112131         36        28329            9                1          0       25
	process_monitor_probe        kgollan-pc  ncc-conductor                2      79691         13        20219            3                1          0       17
	process_monitor_probe        kgollan-pc  node-manager                 2     128951         40        32534           10                4          0       82
	process_monitor_probe        kgollan-pc  routing_engine               0     257895         44        64770           11                1          0       58
	re_interface_manager         kgollan-pc  routing_engine               4       3555          1         1185            0                2          0        4
	snmp_probe_agent_if_mib      kgollan-pc  routing_engine               3      93237          1        69949            0                1          1       13
	snmp_probe_agent_ip_mib      kgollan-pc  routing_engine               3      14096          0         6458            0                1          0        5
	snmp_probe_agent_system_mib  kgollan-pc  routing_engine               3       5105          1         2747            0                1          1        4
	techsupport_manager          kgollan-pc  routing_engine               3       3537          1         1179            0                1          1        4
	transaction_agent            kgollan-pc  management-engine            3       6190          1         1845            0                1          0      621
	wb_agent.dev                 kgollan-pc  datapath1                    1       6719          1        11357            3                4          0       10
	zebra                        kgollan-pc  routing_engine               4       3561          1         3551            1                1          0        7


.. **Help line:** Displays operational database internal information and statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+
