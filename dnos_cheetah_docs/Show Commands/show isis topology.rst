show isis topology
------------------

**Minimum user role:** viewer

The IS-IS topology view displays a table listing all the IS-IS paths to intermediate systems. You can filter the display to show information per routing level.

To display the IS-IS topology:

**Command syntax: show isis** instance [isis-instance-name] **topology** level [level]

**Command mode:** operational



.. **Note**

	-  use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                      |
+====================+==================================================================================================================================================+
| No filter          | Displays all the paths to ISs.                                                                                                                   |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| isis-instance-name | Displays topology information for a specific IS-IS instance. If you do not specify an instance, information for all instances will be displayed. |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| level              | Displays the topology of the specified level. When not set, the topologies of all the levels are displayed                                       |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis topology
	Instance 7:
	IS-IS paths to level-2 routers that speak IP
	Vertex                         Type          Metric   depth     Next-Hop                       Interface          Parent
	qA
	82.0.0.0/24                    IP internal   0        1                                                           qA(4)
	10.8.8.1/32                    IP internal   0        1                                                           qA(4)
	q9                             TE-IS         10       1         q9                             eth1               qA(4)
	9.8.8.7/32                     IP TE         10       2         q9                             eth1               q9(4)
	q8                             TE-IS         20       1         q9                             eth1               qA(4)
	                                                                TUN71                                             q9(4)
	81.0.0.0/24                    IP TE         20       2         q9                             eth1               q9(4)
	8.8.8.7/32                     IP TE         20       2         q9                             eth1               q8(4)
	                                                                TUN71
	IS-IS paths to level-2 routers that speak IPv6
	Vertex                         Type          Metric   depth     Next-Hop                       Interface          Parent
	qA
	8200::/120                     IP6 internal  0        1                                                           qA(4)
	1111::1001/128                 IP6 internal  0        1                                                           qA(4)
	q9                             TE-IS         10       1         q9                             eth1               qA(4)
	1111::9007/128                 IP6 internal  10       2         q9                             eth1               q9(4)
	q8                             TE-IS         20       2         q9                             eth1               q9(4)
	8100::/120                     IP6 internal  20       2         q9                             eth1               q9(4)
	1111::8887/128                 IP6 internal  20       3         q9                             eth1               q8(4)

	Instance 9:
	IS-IS paths to level-2 routers that speak IP
	Vertex                         Type          Metric   depth     Next-Hop                       Interface          Parent
	qA
	83.0.0.0/24                    IP internal   0        1                                                           qA(4)
	10.8.8.1/32                    IP internal   0        1                                                           qA(4)
	qB                             TE-IS         10       1         qB                             eth2               qA(4)
	11.8.8.9/32                    IP TE         10       2         qB                             eth2               qB(4)
	q8                             TE-IS         20       1         qB                             eth2               qA(4)
	                                                                auto_tunnel_R1_R8_PRIORITY_COR
	                                                                E_TUNNELS_1                                       qB(4)
	84.0.0.0/24                    IP TE         20       2         qB                             eth2               qB(4)
	8.8.8.7/32                     IP TE         20       2         qB                             eth2               q8(4)
	                                                                auto_tunnel_R1_R8_PRIORITY_COR
	                                                                E_TUNNELS_1
	8.8.8.9/32                     IP TE         20       2         qB                             eth2               q8(4)
	                                                                auto_tunnel_R1_R8_PRIORITY_COR
	                                                                E_TUNNELS_1

.. **Help line:**

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Removed level filter |
+---------+----------------------+
| 14.0    | Added level filter   |
+---------+----------------------+


