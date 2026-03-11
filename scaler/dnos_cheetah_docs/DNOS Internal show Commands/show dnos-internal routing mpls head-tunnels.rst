show dnos-internal routing mpls head-tunnels
-----------------------------------------------

**Minimum user role:** viewer

To display the RIB MPLS-TE head tunnel database:

**Command syntax:show dnos-internal routing mpls tunnels** {name [tunnel-name] \| destination [ip-address]}

**Command mode:** operation

**Parameter table**

+----------------+-------------------------------------------------------------------------------+-----------------------------+
|                |                                                                               |                             |
| Parameter      | Description                                                                   | Range                       |
+================+===============================================================================+=============================+
|                |                                                                               |                             |
| tunnel-name    | Filter the displayed information to the specified tunnel name                 | String 0..255 characters    |
+----------------+-------------------------------------------------------------------------------+-----------------------------+
|                |                                                                               |                             |
| ip-address     | Filter the displayed information to the specified destination   IP-address    | A.B.C.D                     |
+----------------+-------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show dnos-internal routing mpls head-tunnels
	Tunnel database (size: 583):
	-------------------------------
	OID: 2, HEAD: core_mp1_1
	Destination: 100.0.0.1/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1002
	TE-Class: 0, LSP-OID: 1393 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	OID: 3, HEAD: core_mp2_1
	Destination: 100.0.0.2/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1000
	TE-Class: 0, LSP-OID: 1394 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	OID: 4, HEAD: core_mp3_1
	Destination: 100.0.0.3/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1001
	TE-Class: 0, LSP-OID: 1395 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	OID: 5, HEAD: core_mp4_1
	Destination: 100.0.0.4/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1003
	TE-Class: 0, LSP-OID: 1396 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	OID: 6, HEAD: core_mp5_1
	Destination: 100.0.0.5/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1004
	TE-Class: 0, LSP-OID: 1397 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	dnRouter# show dnos-internal routing mpls head-tunnels name core_mp1_1
	Tunnel database (size: 583):
	-------------------------------
	OID: 2, HEAD: core_mp1_1
	Destination: 100.0.0.1/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1002
	TE-Class: 0, LSP-OID: 1393 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

	dnRouter# show dnos-internal routing mpls head-tunnels destination 10.0.0.2
	Tunnel database (size: 583):
	-------------------------------
	OID: 3, HEAD: core_mp2_1
	Destination: 100.0.0.2/32, In Label: ---, Nexthop: 50.170.0.0 via bundle-502, Out Label: 1000
	TE-Class: 0, LSP-OID: 1394 [0, 0, 0], Flags: 0x1, Ref count: 3, Protection: NONE, MP Label: ---

.. **Help line:** Displays RIB MPLS-TE head tunnel database

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.2.3      | Command introduced    |
+-------------+-----------------------+


