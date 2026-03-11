show dnos-internal routing mpls table oid
-----------------------------------------------

**Minimum user role:** viewer

To display MPLS routing solutions based on nexthop-OID:

**Command syntax:show dnos-internal routing mpls table oid** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing mpls table oid
	Codes: S - static, B - BGP, L - LDP, R - RSVP,
       > - selected route, * - FIB route, (S) - stale route
       (L) - over limit route

	B>*    131072 [20/0] via 100.0.0.164 (recursive) label 3071 (oid: 989), 00:00:19
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.164_IXIA_TUNNELS-CORE_02_203, 00:00:
	19
	B>*    131328 [20/0] via 100.0.0.167 (recursive) label 3027 (oid: 992), 00:00:19
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.167_IXIA_TUNNELS-CORE_02_212, 00:00:
	19
	B>*    131584 [20/0] via 100.0.0.169 (recursive) label 3083 (oid: 994), 00:00:20
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.169_IXIA_TUNNELS-CORE_02_172, 00:00:
	20
	B>*    131840 [20/0] via 100.0.0.172 (recursive) label 3039 (oid: 997), 00:00:20
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.172_IXIA_TUNNELS-CORE_02_178, 00:00:
	20
	B>*    132096 [20/0] via 100.0.0.174 (recursive) label 3095 (oid: 999), 00:00:20
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.174_IXIA_TUNNELS-CORE_02_182, 00:00:
	20
	B>*    132352 [20/0] via 100.0.0.177 (recursive) label 3051 (oid: 1003), 00:00:21
	  *                    via auto_tunnel_Hen-Cluster-Doing-Coverage_100.0.0.177_IXIA_TUNNELS-CORE_02_43, 00:00:2

.. **Help line:** Displays mpls routing solutions based on nexthop-OID

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+


