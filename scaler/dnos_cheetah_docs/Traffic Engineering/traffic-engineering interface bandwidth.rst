traffic-engineering interface bandwidth
---------------------------------------

**Minimum user role:** operator

By default, an interface that is TE enabled, reserves 75% of the interface's bandwidth capacity. You can change the maximum limit for bandwidth reservation for TE on an interface. This limit may exceed the physical limit of the interface. 

All sub-interface of the same physical or bundle interface must be set with the same bandwidth value. Sub-interfaces share the physical or bundle TE bandwidth resource. When allocating a tunnel over one sub-interface, it also deducts from the available bandwidth in other sub-interfaces. Tunnel allocation in different sub-interfaces can cause preemption in other sub-interfaces. 

When explicitly configuring an interface with bandwidth (an absolute value or percentage) it won't share CAC with other sub-interfaces of the same physical/bundle. When allocating a tunnel to an interface, it will not deduct from the available bandwidth in other sub-inetrfaces and vise versa.

-	If you configure an interface with a bandwidth value of 0, no tunnels will use the interface, including 0 bandwidth tunnels.

-	For n <= m, the bandwidth of class-type n must be equal or greater than the bandwidth of class-type m.

-	Tunnel of class-type n can only allocate bandwidth from class-type n, n+1, n+2,… pools.

-	When configuring bandwidth with percent, both class-types must be configured with percent.

-	When traffic-engineering diffserv-te admin-state is enabled, and you want to configure bandwidth for a specifc interface, you must configure bandwidth for all class-types.

-	When traffic-engineering diffserv-te admin-state is disabled, bandwidth for class-type 1 must not be configured (you can only configure bandwidth for class-type 0)


To set a maximum bandwidth reservation limit:


**Command syntax: bandwidth {[bandwidth] [type] \| percent [bw-percent]}** class-type [ct-id]

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering interface

**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle
	
	- Bundle vlan

..
	**Internal Note**

	-  considering **bandwidth units,** total bandwidth amount cannot exceed 4294967295 kbps. i.e for mbps max range is 4194303, for gbps 4096

	-  **percent -** the TE available bandwidth on the interface, relative to the physical interface bandwidth, in %. When a LAG interface accumulated speed changes, TE reserved bandwidth will change accordingly

	-  when configuring bandwidth with percent, both class-types must be configured with percent

	-  when traffic-engineering diffserv-te admin-state is enabled, and user wishes to configure bandwidth for a specifc interface, user must configure bandwidth for all class-types

	-  when traffic-engineering diffserv-te admin-state is disabled, bandwidth for class-type 1 must not be configured (user can only configure bandwidth for class-type 0)

	-  default system behavior for traffic-engineering enabled interface is bandwidth percent 75

	-  when setting interface with 0 value bandwidth, no tunnels will use the interface including 0 bw tunnels

	-  When traffic-engineering diffseerv-te is enabled, bandwidth allocation is according to diffserv-te bandwidth-model

	-  If class-type isn't specified, configure for class-type 0

	-  For n =< m, bandwidth of class-type n must be equal or greater than bandwidth of class-type m

	-  Tunnel of class-type n can only allocate bandwidth from class-type n, n+1, n+2,. pools


	-  different sub interfaces of same physical/bundle can have different shared-cac configuration. i.e some will share cac while others will not

	-  Shared CAC -> Non Shared CAC: Adding interface bandwidth configuration when non exist (using default): Only the reconfigured interface CAC is re-added the bw occupied by shared logic (resulting in increased available bandwidth). If the new configured bandwidth now can't hold all the existing LSPs over the reconfigured interface, preemption will happen as any case of bw change. If no bw change or bw was simply increased, no change for existing LSPs over the reconfigured interface.

	-  Non Shared CAC -> Shared CAC: Removing interface bandwidth (resulting in using default bandwidth): CAC is cleared for the reconfigured interface, leading to soft/hard preemption for all LSPs over that interface (according to rsvp preemption config). All shared-cac sub interfaces of same same physical/bundle will not result in CAC change and no effect of LSPs using these interfaces. If as a result of preemption new LSPs now take bandwidth from the shared CAC interfaces, other LSP preemption may happen based on priority logic. Any new bw reservation on one of the share-cac sub-interfaces will be done accoding to share-cac logic.

**Parameter table**

+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------------------------------+
|                  |                                                                                                                                                                                                                                          |                        |                                             |
| Parameter        | Description                                                                                                                                                                                                                              | Range                  | Default                                     |
+==================+==========================================================================================================================================================================================================================================+========================+=============================================+
|                  |                                                                                                                                                                                                                                          |                        |                                             |
| bandwidth        | The TE available bandwidth on the interface. The   allocated bandwidth is not limited by the physical capacity of the physical   interface. You may allocate more bandwidth than the physical interface allows   (over-subscription).    | 0..4294967295 for kbps | As traffic-engineering bandwidth setting    |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  |                                                                                                                                                                                                                                          | 0..4194303 for mbps    |                                             |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  |                                                                                                                                                                                                                                          | 0..4095 for gbps       |                                             |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------------------------------+
|                  |                                                                                                                                                                                                                                          |                        |                                             |
| unit             | The unit of measurement for the bandwidth.                                                                                                                                                                                               | kbps                   | As traffic-engineering bandwidth setting    |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  |                                                                                                                                                                                                                                          | mbps                   |                                             |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  |                                                                                                                                                                                                                                          | gbps                   |                                             |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------------------------------+
|                  |                                                                                                                                                                                                                                          |                        |                                             |
| bw-percent       | The TE available bandwidth on the interface   relative to the physical interface bandwidth (in %). When used on a bundle   interface, if one of the links drops, the TE reserved bandwidth will change   accordingly.                    | 0..10000               | As traffic-engineering bandwidth setting    |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------------------------------+
|                  |                                                                                                                                                                                                                                          |                        |                                             |
| class-type-id    | Set bandwidth to a specific bandwidth pool.                                                                                                                                                                                              | 0                      | 0                                           |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  | Class-type 0 is the global bandwidth pool (bc0).   If class-type is not specified, the configuration will be applied to   class-type 0.                                                                                                  | 1                      |                                             |
|                  |                                                                                                                                                                                                                                          |                        |                                             |
|                  | For any class-type other than 0, the bandwidth   constraint is only relevant if diffserv-te is enabled. See "show mpls   traffic-engineering diffserv-te".                                                                               |                        |                                             |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1
	dnRouter(cfg-mpls-te-if)# bandwidth 102400 kbps


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-1
	dnRouter(cfg-mpls-te-if)# bandwidth 100 gbps


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-2
	dnRouter(cfg-mpls-te-if)# bandwidth percent 100

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-3
	dnRouter(cfg-mpls-te-if)# bandwidth percent 95


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# interface bundle-4
	dnRouter(cfg-mpls-te-if)# bandwidth percent 125

**Removing Configuration**

To revert bandwidth restrictions to the default values for all classes:
::

	dnRouter(cfg-mpls-te-if)# no bandwidth

To revert to the default bandwidth value for class-type 1:
::

	dnRouter(cfg-mpls-te-if)# no bandwidth percent 95 class-type 1
	dnRouter(cfg-mpls-te-if)# no bandwidth 1000 mbps class-type 1


To revert to the default bandwidth value for class-type 0:
::

	dnRouter(cfg-mpls-te-if)# no bandwidth percent 90 class-type 0
	dnRouter(cfg-mpls-te-if)# no bandwidth percent 95
	dnRouter(cfg-mpls-te-if)# no bandwidth percent
	dnRouter(cfg-mpls-te-if)# no bandwidth 900 mbps class-type 0
	dnRouter(cfg-mpls-te-if)# no bandwidth 1000 mbps
	dnRouter(cfg-mpls-te-if)# no bandwidth 1000


.. **Help line:**

**Command History**

+-------------+----------------------------------------------------------------------+
|             |                                                                      |
| Release     | Modification                                                         |
+=============+======================================================================+
|             |                                                                      |
| 9.0         | Command introduced                                                   |
+-------------+----------------------------------------------------------------------+
|             |                                                                      |
| 10.0        | Added the ability to configure bandwidth limits   per class-type.    |
+-------------+----------------------------------------------------------------------+