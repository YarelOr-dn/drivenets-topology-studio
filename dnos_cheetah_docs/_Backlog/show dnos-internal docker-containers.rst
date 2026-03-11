show dnos-internal docker-containers
------------------------------------

**Command syntax: show dnos-internal docker-containers**

**Description:** Display status of docker swarm and docker containers in cluster

**CLI example:**
::

	dnRouter# show dnos-internal docker-containers
	List of nodes in the swarm:
	ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
	vn2oactbapdwn5edb2owzoliw     WDY194740000C       Ready               Active              Reachable
	08riff0x29dqqbgibdjwsquzd     WDY1947200026       Ready               Active              Reachable
	si79psk82whttrx5hqnd2jcmf     WEB1947400017       Ready               Active              Reachable
	qyl316jmz9ziiwe37sx240zcd *   dn43-re0            Ready               Active              Leader
	y50dyh83yfr4azu0cwo8my1tn     dn43-re1            Ready               Active              Reachable

	List of containers in DNOS cluster:
	CONTAINER ID        IMAGE                                                                                         COMMAND                  CREATED             STATUS              PORTS                    NAMES
	e7117c34f91f        pr-registry.dev.drivenets.net/me_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv             "/usr/local/bin/du..."   About an hour ago   Up About an hour    0.0.0.0:514->514/udp     casdasasdabha_management-engine.1.he39y8b69t45y1152du5zi2qd
	4a85f868b7f8        pr-registry.dev.drivenets.net/me_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv             "/usr/local/bin/du..."   About an hour ago   Up About an hour                             casdasasdabha_management-engine-fetch.qyl316jmz9ziiwe37sx240zcd.9lmzlm2h5dtrx3f0q7wjhq6nd
	de623b316c90        pr-registry.dev.drivenets.net/re_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv             "/usr/local/bin/du..."   About an hour ago   Up About an hour    0.0.0.0:6379->6379/tcp   casdasasdabha_manager.qyl316jmz9ziiwe37sx240zcd.l2lb5g8kbk8wg5to64y90pqqh
	7bf10df1b592        pr-registry.dev.drivenets.net/node_manager_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv   "/usr/local/bin/du..."   About an hour ago   Up About an hour    0.0.0.0:5100->5100/tcp   casdasasdabha_node-manager.qyl316jmz9ziiwe37sx240zcd.e901j49e4aiqyp1a0gf157esh
	c98502b841bf        registry.dev.drivenets.net/dn_redis_all:5.0.5-6                                               "/usr/bin/dumb-ini..."   About an hour ago   Up About an hour                             casdasasdabha_redis_sentinel.qyl316jmz9ziiwe37sx240zcd.w6ebjb8w63kmh7lf8lnuo5r0n
	1370dc60d7b6        registry.dev.drivenets.net/dn_redis_all:5.0.5-6                                               "/usr/bin/dumb-ini..."   About an hour ago   Up About an hour                             casdasasdabha_redis.qyl316jmz9ziiwe37sx240zcd.jqchpbqr42wezh34j0dm6wjrb
	b66baaa99907        registry.dev.drivenets.net/dn_redis_all:5.0.5-6                                               "/usr/bin/dumb-ini..."   About an hour ago   Up About an hour                             casdasasdabha_redis_config.qyl316jmz9ziiwe37sx240zcd.huj4atyoc6n1as6j67n7tqxn4

	List of running services in DNOS cluster:
	ID                  NAME                                    MODE                REPLICAS            IMAGE                                                                                         PORTS
	s7l1ulm8ld5l        casdasasdabha_datapath                  global              3/3                 pr-registry.dev.drivenets.net/wb_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv
	oezzx30c7f56        casdasasdabha_management-engine         replicated          1/1                 pr-registry.dev.drivenets.net/me_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv             *:22->2223/tcp,*:830->830/tcp
	1k5gu1z669a8        casdasasdabha_management-engine-fetch   global              2/2                 pr-registry.dev.drivenets.net/me_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv
	sgbnal7wttdm        casdasasdabha_manager                   global              2/2                 pr-registry.dev.drivenets.net/re_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv
	ye93r3cqhphc        casdasasdabha_ncc-conductor             replicated          1/1                 pr-registry.dev.drivenets.net/me_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv             *:443->443/tcp,*:4505->4505/tcp,*:4506->4506/tcp,*:5000->80/tcp,*:5200->5100/tcp
	y8bre7kbo3k7        casdasasdabha_ncc-selector              replicated          1/1                 pr-registry.dev.drivenets.net/node_manager_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv
	3l3a2xitzvdq        casdasasdabha_node-manager              global              5/5                 pr-registry.dev.drivenets.net/node_manager_dev_v11_cnt_check_remove_sub_locks:11.0.0.8_priv
	h9cpk1dal8v6        casdasasdabha_redis                     global              1/1                 registry.dev.drivenets.net/dn_redis_all:5.0.5-6
	pj54fpm67gen        casdasasdabha_redis_config              global              1/1                 registry.dev.drivenets.net/dn_redis_all:5.0.5-6
	jsss4pl2n0r4        casdasasdabha_redis_sentinel            global              5/5                 registry.dev.drivenets.net/dn_redis_all:5.0.5-6
	6zkcdc05udca        casdasasdabha_redis_slave               global              1/1                 registry.dev.drivenets.net/dn_redis_all:5.0.5-6
	hsi90poe61mh        casdasasdabha_redis_slave_config        global              1/1                 registry.dev.drivenets.net/dn_redis_all:5.0.5-6



**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:**

Display status of docker swarm and docker containers in cluster

**Parameter table:**
