bgp neighbor address-family unicast llgr stalepath-time - N/A for this version
------------------------------------------------------------------------------

**Command syntax: stalepath-time [time]** [units]

**Description:** Set how long a neighbor router will wait before deleting stale routes after an EoR message is received from the restarting LLGR capable router. The stalepath-time timer starts after the graceful-restart stalepath-time expires.

Local stale time is set according to neighbor requested saltepath-time.

**CLI example:**
::

	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
	dnRouter(cfg-bgp-neighbor-afi)# llgr enabled
	dnRouter(cfg-bgp-neighbor-afi-llgr)# stalepath-time 90 minutes
	
	dnRouter#
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp 65000
	dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
	dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
	dnRouter(cfg-bgp-neighbor-afi)# llgr enabled
	dnRouter(cfg-bgp-neighbor-afi-llgr)# stalepath-time 3
	
	
	dnRouter(cfg-bgp-neighbor-afi-llgr)# no stalepath-time
	
**Command mode:** config

**TACACS role:** operator

**Note:**

no command returns stalepath-time to default value

if during stalepath-time the local bgp router restart, the stale routes will be removed even if nsr is enabled.

**Help line:**

**Parameter table:**

+-----------+-------------------------------+---------------+
| Parameter | Values                        | Default value |
+===========+===============================+===============+
| time      | 1..16777215 for seconds       | 1 days        |
|           |                               |               |
|           | 1..279620 for minutes         |               |
|           |                               |               |
|           | 1..4660 for hours             |               |
|           |                               |               |
|           | 1..194 for days               |               |
+-----------+-------------------------------+---------------+
| units     | seconds, minutes, hours, days | days          |
+-----------+-------------------------------+---------------+
