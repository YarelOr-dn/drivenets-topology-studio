show rsvp cac-reservation
-------------------------

**Minimum user role:** viewer

This command is applicable to the following interfaces:

physical interfaces logical interfaces (sub-interfaces) bundle interfaces bundle sub-interfaces

To display connection admission control (CAC) bandwidth reservation by RSVP tunnels:

**Command syntax: show rsvp cac-reservation** interface [interface-name]

**Command mode:** operational



**Note**

- Tail tunnels do not reserve bandwidth and are therefore not displayed.

- The DNOS RSVP reservation style is Shared Explicit.

**Parameter table**

+----------------+-----------------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter      | Description                                                                       | Range                                              | Default |
+================+===================================================================================+====================================================+=========+
| interface-name | Displays only the tunnels whose egress interface matches the specified interface. | ge<interface speed>-<A>/<B>/<C>                    | \-      |
|                |                                                                                   |                                                    |         |
|                |                                                                                   | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |         |
|                |                                                                                   |                                                    |         |
|                |                                                                                   | bundle-<bundle id>                                 |         |
|                |                                                                                   |                                                    |         |
|                |                                                                                   | bundle-<bundle id>.<sub-interface id>              |         |
+----------------+-----------------------------------------------------------------------------------+----------------------------------------------------+---------+

The following information is displayed per tunnel:

+------------------+----------------------------------------------------+
| Parameter        | Description                                        |
+==================+====================================================+
| Destination      | The tunnel's destination address                   |
+------------------+----------------------------------------------------+
| Tunnel-id/Lsp-id | The tunnel's identification and LSP identification |
+------------------+----------------------------------------------------+
| Ingress-if       | The tunnel's ingress interface                     |
+------------------+----------------------------------------------------+
| Egress-if        | The tunnel's egress interface                      |
+------------------+----------------------------------------------------+
| CT               | The tunnel's class type                            |
+------------------+----------------------------------------------------+
| HP               | The tunnel's hold priority                         |
+------------------+----------------------------------------------------+
| BW [kbps]        | The tunnel's requested bandwidth                   |
+------------------+----------------------------------------------------+
| State            | The bandwidth reservation state:                   |
|                  | resv - bandwidth reserved                          |
|                  | held - bandwidth held waiting reservation          |
|                  | softp - bandwidth soft preempted                   |
+------------------+----------------------------------------------------+
| Name             | The tunnel's name                                  |
+------------------+----------------------------------------------------+

**Example**
::

	dnRouter# show rsvp cac-reservation

	| Destination     | Tunnel-id | Lsp-id   | Ingress-if      | Egress-if       | CT | HP | BW [kbps]    | State | Name                                     |
	+-----------------+-----------+----------+-----------------+-----------------+----+----+--------------+-------+------------------------------------------|
	| 10.0.0.117      | 12        | 841      | bundle-1.2      | bundle-2.1      | 0  | 5  | 1            | held  | Tunnel_WB15_WB11_Default                 |
	| 10.189.201.13   | 22        | 22       | -               | bundle-13.1     | 1  | 3  | 1000         | resv  | Tunnel_WB11_WB03_Primary                 |
	| 10.189.201.13   | 30        | 664      | bundle-11       | bundle-13.1     | 1  | 3  | 1000         | resv  | Tunnel_WB01_WB03_Primary                 |


	dnRouter# show rsvp cac-reservation interface bundle-13.1

	| Destination     | Tunnel-id | Lsp-id   | Ingress-if      | Egress-if       | CT | HP | BW [kbps]    | State | Name                                     |
	+-----------------+-----------+----------+-----------------+-----------------+----+----+--------------+-------+------------------------------------------|
	| 10.189.201.13   | 22        | 22       | -               | bundle-13.1     | 1  | 3  | 1000         | resv  | Tunnel_WB11_WB03_Primary                 |
	| 10.189.201.13   | 30        | 664      | bundle-11       | bundle-13.1     | 1  | 3  | 1000         | resv  | Tunnel_WB01_WB03_Primary                 |


.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
