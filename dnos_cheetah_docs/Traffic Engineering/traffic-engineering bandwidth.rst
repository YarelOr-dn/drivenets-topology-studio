traffic-engineering bandwidth
-----------------------------

**Minimum user role:** operator

By default, an interface that is TE enabled, reserves 75% of the interface's bandwidth capacity. You can change the maximum limit for bandwidth reservation for TE on an interface per type-class. This limit may exceed the physical limit of the interface.

All sub-interface of the same physical or bundle interface must be set with the same bandwidth value. Sub-interfaces share the physical or bundle TE bandwidth resource. When allocating a tunnel over one sub-interface, it also deducts from the available bandwidth in other sub-interfaces. Tunnel allocation in different sub-interfaces can cause preemption in other sub-interfaces.

When explicitly configuring an interface with bandwidth (an absolute value or percentage) it won't share CAC with other sub-interfaces of the same physical/bundle. When allocating a tunnel to an interface, it will not deduct from the available bandwidth in other sub-inetrfaces and vise versa.

To set a maximum bandwidth reservation limit:

**Command syntax: bandwidth {[bandwidth] [type] \| percent [bw-percent]}** class-type [ct-id]

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

-	For n =< m, the bandwidth of class-type n must be equal or greater than the bandwidth of class-type m.

-	Tunnel of class-type n can only allocate bandwidth from class-type n, n+1, n+2,… pools.

**Parameter table**

+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------+
|                  |                                                                                                                                                                                                                                          |                        |                     |
| Parameter        | Description                                                                                                                                                                                                                              | Range                  | Default             |
+==================+==========================================================================================================================================================================================================================================+========================+=====================+
|                  |                                                                                                                                                                                                                                          |                        |                     |
| bandwidth        | The TE available bandwidth on the interface. The   allocated bandwidth is not limited by the physical capacity of the physical   interface. You may allocate more bandwidth than the physical interface allows   (over-subscription).    | 0..4294967295 for kbps | \-                  |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  |                                                                                                                                                                                                                                          | 0..4194303 for mbps    |                     |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  |                                                                                                                                                                                                                                          | 0..4095 for gbps       |                     |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------+
|                  |                                                                                                                                                                                                                                          |                        |                     |
| unit             | The unit of measurement for the bandwidth.                                                                                                                                                                                               | kbps                   | \-                  |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  |                                                                                                                                                                                                                                          | mbps                   |                     |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  |                                                                                                                                                                                                                                          | gbps                   |                     |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------+
|                  |                                                                                                                                                                                                                                          |                        |                     |
| bw-percent       | The TE available bandwidth on the interface   relative to the physical interface bandwidth (in %). When used on a bundle   interface, if one of the links drops, the TE reserved bandwidth will change accordingly.                      | 0..10000               | Class-type 0: 75%   |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  | Percent is the default setting. When configuring   bandwidth with percent, both class-types must be configured with percent.                                                                                                             |                        | Class-type 1: 0%    |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------+
|                  |                                                                                                                                                                                                                                          |                        |                     |
| class-type-id    | Set bandwidth to a specific bandwidth pool.                                                                                                                                                                                              | 0                      | 0                   |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  | Class-type 0 is the global bandwidth pool (bc0).                                                                                                                                                                                         | 1                      |                     |
|                  |                                                                                                                                                                                                                                          |                        |                     |
|                  | For any class-type other than 0, the bandwidth   constraint is only relevant if diffserv-te is enabled. See "show mpls   traffic-engineering diffserv-te".                                                                               |                        |                     |
+------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+---------------------+

**Example**
::


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-mpls-te)# bandwidth percent 95 class-type 0
	dnRouter(cfg-mpls-te)# bandwidth percent 90 class-type 1

**Removing Configuration**

To revert bandwidth restrictions to the default values for all classes:
::

	dnRouter(cfg-mpls-te)# no bandwidth

To revert to the default bandwidth value for class-type 1:
::

	dnRouter(cfg-mpls-te)# no bandwidth percent 95 class-type 1
	dnRouter(cfg-mpls-te)# no bandwidth 1000 mbps class-type 1


To revert to the default bandwidth value for class-type 0:
::

	dnRouter(cfg-mpls-te)# no bandwidth percent 90 class-type 0
	dnRouter(cfg-mpls-te)# no bandwidth percent 95
	dnRouter(cfg-mpls-te)# no bandwidth percent
	dnRouter(cfg-mpls-te)# no bandwidth 900 mbps class-type 0
	dnRouter(cfg-mpls-te)# no bandwidth 1000 mbps
	dnRouter(cfg-mpls-te)# no bandwidth 1000

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+