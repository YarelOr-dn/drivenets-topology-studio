show system backplane
----------------------

**Minimum user role:** viewer

To display the system backplane connectivity matrix:



**Command syntax: show system backplane** {fabric ncp [ncp-id] \| control ncm [ncm-id] \| fabric stats ncp [ncp-id] }

**Command mode:** operational



**Note**

- The fabric connectivity statistics displays the number of connected fabric links out of the number of expected connections.

- In a small cluster, the number of expected connections is 12 and the number of expected connections in a medium or large cluster is 13.

- In a cluster of NCPs of model NCP-36CD-S, the number of expected connections is up to 40.

- If you have less than 100% of connected interface, check your connections.

- IPMI interfaces are not discovered by the neighbor; their state not displayed.


**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+
| Parameter | Description                                                                                                     | Range          |
+===========+=================================================================================================================+================+
| fabric    | Filters the display to only Fabric connectivity state and Fabric connectivity statistics.                       | \-             |
+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+
| stats     | Filters the display to only Fabric connectivity statistics.                                                     | \-             |
+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+
| ncp-id    | Filters the display to only Fabric connectivity state and Fabric connectivity statistics for the specified NCP. | 0..249         |
+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+
| control   | Filters the display to only Control connectivity state                                                          | \-             |
+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+
| ncm-id    | Filters the display to only Control connectivity state for the specified NCM                                    | A0, B0, A1, B1 |
+-----------+-----------------------------------------------------------------------------------------------------------------+----------------+

For each interface, the following information is displayed:

+--------------------------------+--------------------------------------------------------------------------------------------------------------+
| Field                          | Description                                                                                                  |
+================================+==============================================================================================================+
| System Type                    | SA-40C                                                                                                       |
|                                | SA-10CD                                                                                                      |
|                                | CL-16                                                                                                        |
|                                | CL-32                                                                                                        |
|                                | CL-48                                                                                                        |
|                                | CL-49                                                                                                        |
|                                | CL-51                                                                                                        |
|                                | CL-64                                                                                                        |
|                                | CL-76                                                                                                        |
|                                | CL-86                                                                                                        |
|                                | CL-96                                                                                                        |
|                                | CL-153                                                                                                       |
|                                | CL-192                                                                                                       |
|                                | CL-409                                                                                                       |
|                                | CL-768                                                                                                       |
|                                | CL-AI-8K-400G                                                                                                |
|                                | AI-256-400G-2                                                                                                |
|                                | AI-72-800G-2                                                                                                 |
|                                | AI-8192-400G-2                                                                                               |
+--------------------------------+--------------------------------------------------------------------------------------------------------------+
| Supported element scale        | Displays the number of elements forming the cluster. See table below.                                        |
+--------------------------------+--------------------------------------------------------------------------------------------------------------+
| Fabric connectivity state      | For each NCP, displays which fabric port is connected to which NCF port                                      |
+--------------------------------+--------------------------------------------------------------------------------------------------------------+
| Fabric connectivity statistics | Displays the number of NCP-to-NCF connections with connection state OK                                       |
+--------------------------------+--------------------------------------------------------------------------------------------------------------+
| Control connectivity state     | For each NCM, displays which control port is connected to where.                                             |
+--------------------------------+--------------------------------------------------------------------------------------------------------------+

The elements forming each cluster type:

+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| Model Name     | Description                                                                                                                              |
+================+==========================================================================================================================================+
| SA-40C         | A standalone NCP with 40 ports of 100 Gbps (= 4 Tbps).                                                                                   |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| SA-10CD        | A standalone NCP with 10 ports of 400 Gbps (= 4 Tbps).                                                                                   |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-16          | A small cluster with a total capacity of 16 Tbps (given that the supported NCPs are both of 4 Tbps, then this cluster comprises 4 NCPs). |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-32          | A small cluster with a total capacity of 32 Tbps (given that the supported NCPs are of 4 Tbps, then this cluster comprises 8 NCPs).      |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-48          | A small cluster with a total capacity of 48 Tbps (given that the supported NCPs are of 4 Tbps, then this cluster comprises 12 NCPs).     |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-49          | A small cluster with a total capacity of 49.6 Tbps (supports up to 4 NCP-Lite and 10 NCP-1/2 platforms).                                 |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-51          | A small cluster with a total capacity of 51.2 Tbps (given that the supported NCPs are of 12.8 Tbps, then this cluster comprises 4 NCPs). |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-64          | A small cluster with a total capacity of 64 Tbps (given that the supported NCPs are of 4 Tbps, then this cluster comprises 16 NCPs).     |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-76          | A small cluster with a total capacity of 76.8 Tbps (given that the supported NCPs are of 12.8 Tbps, then this cluster comprises 6 NCPs). |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-86          | A medium cluster with a total capacity of 86.4 Tbps (supports up to 6 NCP-Lite and 18 NCP-1/2 platforms).                                |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-96          | A medium cluster with a total capacity of 96 Tbps (i.e. 24 NCPs).                                                                        |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-153         | A large cluster - up to 12xNCP interconnected via 10xNCF-48 + two NCCs                                                                   |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-192         | A large cluster - up to 48xNCP interconnected via 13xNCF-48 + two NCCs                                                                   |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-409         | A very large cluster - up to 32xNCP-3 interconnected via 36xNCF-48 + two NCCs                                                            |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| CL-AI-8K-400G  | An extra large cluster - up to 250x NCP interconnected via 612x NCF-48 in three-stage mode                                               |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| AI-256-400G-2  | A small AI cluster - up to 8x NCP5 interconnected via 2x NCF2                                                                            |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| AI-72-800G-2   | A small AI cluster - up to 4x NCP5 interconnected via 1x NCF2                                                                            |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+
| AI-8192-400G-2 | An extra large cluster - up to 256x NCP5 interconnected via 36x NCF2                                                                     |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------+

The connection states are:

+------------------+----------------------------------+
| Connection State | Description                      |
+==================+==================================+
| OK               | The connection is up as expected |
+------------------+----------------------------------+
| Error            | Connected not as expected        |
+------------------+----------------------------------+
| Not connected    |                                  |
+------------------+----------------------------------+

**Example**
::

	dnRouter# show system backplane

	System Type: CL-16
	Supported element scale: NCC:2, NCF:1, NCP:4, NCM:2

	Fabric Connectivity Statistics:

	NCP-0 : 7/12  (58.8 % of the expected fabric interfaces are connected)
	NCP-1 : 8/12  (66.7 % of the expected fabric interfaces are connected)
	NCP-2 : 10/12 (83.3 % of the expected fabric interfaces are connected)
	NCP-3 : 12/12 (100 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-0:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-0/0/0      | fab-ncf400-0/0/36           | fab-ncf400-0/0/36           | ok                |
	| fab-ncp400-0/0/1      | fab-ncf400-0/0/37           |                             | not-connected     |
	| fab-ncp400-0/0/2      | fab-ncf400-0/0/38           | fab-ncf400-0/0/38           | ok                |
	| fab-ncp400-0/0/3      | fab-ncf400-0/0/39           | fab-ncf400-0/0/40           | error             |
	| fab-ncp400-0/0/4      | fab-ncf400-0/0/40           | fab-ncf400-0/0/39           | error             |
	| fab-ncp400-0/0/5      | fab-ncf400-0/0/41           | fab-ncf400-0/0/41           | ok                |
	| fab-ncp400-0/0/6      | fab-ncf400-0/0/42           | fab-ncf400-0/0/42           | ok                |
	| fab-ncp400-0/0/7      | fab-ncf400-0/0/43           | fab-ncf400-0/0/43           | ok                |
	| fab-ncp400-0/0/8      | fab-ncf400-0/0/44           |                             | not-connected     |
	| fab-ncp400-0/0/9      | fab-ncf400-0/0/45           | fab-ncf400-0/0/45           | ok                |
	| fab-ncp400-0/0/10     | fab-ncf400-0/0/46           |                             | not-connected     |
	| fab-ncp400-0/0/11     | fab-ncf400-0/0/47           | fab-ncf400-0/0/47           | ok                |
	| fab-ncp400-0/0/12     |                             |                             |                   |

	NCP-1:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-1/0/0      | fab-ncf400-0/0/24           | fab-ncf400-0/0/24           | ok                |
	| fab-ncp400-1/0/1      | fab-ncf400-0/0/25           |                             | not-connected     |
	| fab-ncp400-1/0/2      | fab-ncf400-0/0/26           | fab-ncf400-0/0/26           | ok                |
	| fab-ncp400-1/0/3      | fab-ncf400-0/0/27           | fab-ncf400-0/0/28           | error             |
	| fab-ncp400-1/0/4      | fab-ncf400-0/0/28           | fab-ncf400-0/0/27           | error             |
	| fab-ncp400-1/0/5      | fab-ncf400-0/0/29           | fab-ncf400-0/0/29           | ok                |
	| fab-ncp400-1/0/6      | fab-ncf400-0/0/30           | fab-ncf400-0/0/30           | ok                |
	| fab-ncp400-1/0/7      | fab-ncf400-0/0/31           | fab-ncf400-0/0/31           | ok                |
	| fab-ncp400-1/0/8      | fab-ncf400-0/0/32           |                             | not-connected     |
	| fab-ncp400-1/0/9      | fab-ncf400-0/0/33           | fab-ncf400-0/0/33           | ok                |
	| fab-ncp400-1/0/10     | fab-ncf400-0/0/34           | fab-ncf400-0/0/34           | ok                |
	| fab-ncp400-1/0/11     | fab-ncf400-0/0/35           | fab-ncf400-0/0/35           | ok                |
	| fab-ncp400-0/0/12     |                             |                             |                   |

	NCP-2:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-2/0/0      | fab-ncf400-0/0/0            | fab-ncf400-0/0/0            | ok                |
	| fab-ncp400-2/0/1      | fab-ncf400-0/0/1            | fab-ncf400-0/0/1            | ok                |
	| fab-ncp400-2/0/2      | fab-ncf400-0/0/2            | fab-ncf400-0/0/2            | ok                |
	| fab-ncp400-2/0/3      | fab-ncf400-0/0/3            | fab-ncf400-0/0/3            | ok                |
	| fab-ncp400-2/0/4      | fab-ncf400-0/0/4            | fab-ncf400-0/0/4            | ok                |
	| fab-ncp400-2/0/5      | fab-ncf400-0/0/5            | fab-ncf400-0/0/5            | ok                |
	| fab-ncp400-2/0/6      | fab-ncf400-0/0/6            | fab-ncf400-0/0/6            | ok                |
	| fab-ncp400-2/0/7      | fab-ncf400-0/0/7            | fab-ncf400-0/0/7            | ok                |
	| fab-ncp400-2/0/8      | fab-ncf400-0/0/8            | fab-ncf400-0/0/8            | ok                |
	| fab-ncp400-2/0/9      | fab-ncf400-0/0/9            | fab-ncf400-0/0/9            | ok                |
	| fab-ncp400-2/0/10     | fab-ncf400-0/0/10           | fab-ncf400-0/0/10           | ok                |
	| fab-ncp400-2/0/11     | fab-ncf400-0/0/11           |                             | not-connected     |
	| fab-ncp400-2/0/12     |                             | fab-ncf400-0/0/11           |                   |

	NCP-3:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-3/0/0      | fab-ncf400-0/0/12           | fab-ncf400-0/0/12           | ok                |
	| fab-ncp400-3/0/1      | fab-ncf400-0/0/13           | fab-ncf400-0/0/13           | ok                |
	| fab-ncp400-3/0/2      | fab-ncf400-0/0/14           | fab-ncf400-0/0/14           | ok                |
	| fab-ncp400-3/0/3      | fab-ncf400-0/0/15           | fab-ncf400-0/0/15           | ok                |
	| fab-ncp400-3/0/4      | fab-ncf400-0/0/16           | fab-ncf400-0/0/16           | ok                |
	| fab-ncp400-3/0/5      | fab-ncf400-0/0/17           | fab-ncf400-0/0/17           | ok                |
	| fab-ncp400-3/0/6      | fab-ncf400-0/0/18           | fab-ncf400-0/0/18           | ok                |
	| fab-ncp400-3/0/7      | fab-ncf400-0/0/19           | fab-ncf400-0/0/19           | ok                |
	| fab-ncp400-3/0/8      | fab-ncf400-0/0/20           | fab-ncf400-0/0/20           | ok                |
	| fab-ncp400-3/0/9      | fab-ncf400-0/0/21           | fab-ncf400-0/0/21           | ok                |
	| fab-ncp400-3/0/10     | fab-ncf400-0/0/22           | fab-ncf400-0/0/22           | ok                |
	| fab-ncp400-3/0/11     | fab-ncf400-0/0/23           | fab-ncf400-0/0/23           | ok                |
	| fab-ncp400-3/0/12     |                             |                             |                   |

	Control Connectivity State:

	NCM-A0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-A0/0   | ipmi-ncf-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/1   |                             |                             |                        |                   |
	| ctrl-ncm-A0/2   |                             |                             |                        |                   |
	| ctrl-ncm-A0/3   |                             |                             |                        |                   |
	| ctrl-ncm-A0/4   | ipmi-ncp-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/5   | ipmi-ncp-2/0                |                             |                        |                   |
	| ctrl-ncm-A0/6   |                             |                             |                        |                   |
	| ctrl-ncm-A0/7   |                             |                             |                        |                   |
	| ctrl-ncm-A0/8   |                             |                             |                        |                   |
	| ctrl-ncm-A0/9   |                             |                             |                        |                   |
	| ctrl-ncm-A0/10  |                             |                             |                        |                   |
	| ctrl-ncm-A0/11  |                             |                             |                        |                   |
	| ctrl-ncm-A0/12  |                             |                             |                        |                   |
	| ctrl-ncm-A0/13  |                             |                             |                        |                   |
	| ctrl-ncm-A0/14  |                             |                             |                        |                   |
	| ctrl-ncm-A0/15  |                             |                             |                        |                   |
	| ctrl-ncm-A0/16  | ctrl-ncf-0/0                | ctrl-ncf-0/0                | 12345                  | ok                |
	| ctrl-ncm-A0/17  | ipmi-ncm-B0/0               |                             |                        |                   |
	| ctrl-ncm-A0/18  |                             |                             |                        |                   |
	| ctrl-ncm-A0/19  |                             |                             |                        |                   |
	| ctrl-ncm-A0/20  |                             |                             |                        |                   |
	| ctrl-ncm-A0/21  |                             |                             |                        |                   |
	| ctrl-ncm-A0/22  |                             |                             |                        |                   |
	| ctrl-ncm-A0/23  |                             |                             |                        |                   |
	| ctrl-ncm-A0/24  | ctrl-ncp-0/0                | ctrl-ncp-0/0                | ABCDE12345             | ok                |
	| ctrl-ncm-A0/25  | ctrl-ncp-1/0                | ctrl-ncp-1/0                | XYZ12345               | ok                |
	| ctrl-ncm-A0/26  | ctrl-ncp-2/0                | ctrl-ncp-x/1                | ABCXYZ                 | error             |
	| ctrl-ncm-A0/27  | ctrl-ncp-3/0                | ctrl-ncp-2/0                | ABCXYZ                 | error             |
	| ctrl-ncm-A0/28  |                             |                             |                        |                   |
	| ctrl-ncm-A0/29  |                             |                             |                        |                   |
	| ctrl-ncm-A0/30  |                             |                             |                        |                   |
	| ctrl-ncm-A0/31  |                             |                             |                        |                   |
	| ctrl-ncm-A0/32  |                             |                             |                        |                   |
	| ctrl-ncm-A0/33  |                             |                             |                        |                   |
	| ctrl-ncm-A0/34  |                             |                             |                        |                   |
	| ctrl-ncm-A0/35  |                             |                             |                        |                   |
	| ctrl-ncm-A0/36  |                             |                             |                        |                   |
	| ctrl-ncm-A0/37  |                             |                             |                        |                   |
	| ctrl-ncm-A0/38  |                             |                             |                        |                   |
	| ctrl-ncm-A0/39  |                             |                             |                        |                   |
	| ctrl-ncm-A0/40  |                             |                             |                        |                   |
	| ctrl-ncm-A0/41  |                             |                             |                        |                   |
	| ctrl-ncm-A0/42  |                             |                             |                        |                   |
	| ctrl-ncm-A0/43  |                             |                             |                        |                   |
	| ctrl-ncm-A0/44  |                             |                             |                        |                   |
	| ctrl-ncm-A0/45  |                             |                             |                        |                   |
	| ctrl-ncm-A0/46  |                             |                             |                        |                   |
	| ctrl-ncm-A0/47  |                             |                             |                        |                   |
	| ctrl-ncm-A0/48  | ctrl-ncc-0/0                |                             |                        | not-connected     |
	| ctrl-ncm-A0/49  | ctrl-ncc-1/0                | ctrl-ncc-1/0                | ABX                    | ok                |
	| ctrl-ncm-A0/50  |                             |                             |                        |                   |
	| ctrl-ncm-A0/51  | ctrl-ncm-B0/51              | ctrl-ncm-B0/51              | AZ876                  | ok                |
	| ctrl-ncm-A0/52  | ctrl-ncm-B0/52              | ctrl-ncm-B0/52              | AZ876                  | ok                |
	| ctrl-ncm-A0/53  |                             |                             |                        |                   |

	NCM-B0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-B0/0   |                             |                             |                        |                   |
	| ctrl-ncm-B0/1   |                             |                             |                        |                   |
	| ctrl-ncm-B0/2   |                             |                             |                        |                   |
	| ctrl-ncm-B0/3   |                             |                             |                        |                   |
	| ctrl-ncm-B0/4   | ipmi-ncp-1/0                |                             |                        |                   |
	| ctrl-ncm-B0/5   | ipmi-ncp-3/0                |                             |                        |                   |
	| ctrl-ncm-B0/6   |                             |                             |                        |                   |
	| ctrl-ncm-B0/7   |                             |                             |                        |                   |
	| ctrl-ncm-B0/8   |                             |                             |                        |                   |
	| ctrl-ncm-B0/9   |                             |                             |                        |                   |
	| ctrl-ncm-B0/10  |                             |                             |                        |                   |
	| ctrl-ncm-B0/11  |                             |                             |                        |                   |
	| ctrl-ncm-B0/12  |                             |                             |                        |                   |
	| ctrl-ncm-B0/13  |                             |                             |                        |                   |
	| ctrl-ncm-B0/14  |                             |                             |                        |                   |
	| ctrl-ncm-B0/15  |                             |                             |                        |                   |
	| ctrl-ncm-B0/16  | ctrl-ncf-0/1                | ctrl-ncf-0/1                | 12345                  | ok                |
	| ctrl-ncm-B0/17  | ipmi-ncm-A0/0               |                             |                        |                   |
	| ctrl-ncm-B0/18  |                             |                             |                        |                   |
	| ctrl-ncm-B0/19  |                             |                             |                        |                   |
	| ctrl-ncm-B0/20  |                             |                             |                        |                   |
	| ctrl-ncm-B0/21  |                             |                             |                        |                   |
	| ctrl-ncm-B0/22  |                             |                             |                        |                   |
	| ctrl-ncm-B0/23  |                             |                             |                        |                   |
	| ctrl-ncm-B0/24  | ctrl-ncp-0/1                | ctrl-ncp-0/1                | ABCDE12345             | ok                |
	| ctrl-ncm-B0/25  | ctrl-ncp-1/1                | ctrl-ncp-1/1                | XYZ12345               | ok                |
	| ctrl-ncm-B0/26  | ctrl-ncp-2/1                | ctrl-ncp-3/1                | ABCXYZ                 | error             |
	| ctrl-ncm-B0/27  | ctrl-ncp-3/1                | ctrl-ncp-2/1                | DBCXYZ                 | error             |
	| ctrl-ncm-B0/28  |                             |                             |                        |                   |
	| ctrl-ncm-B0/29  |                             |                             |                        |                   |
	| ctrl-ncm-B0/30  |                             |                             |                        |                   |
	| ctrl-ncm-B0/31  |                             |                             |                        |                   |
	| ctrl-ncm-B0/32  |                             |                             |                        |                   |
	| ctrl-ncm-B0/33  |                             |                             |                        |                   |
	| ctrl-ncm-B0/34  |                             |                             |                        |                   |
	| ctrl-ncm-B0/35  |                             |                             |                        |                   |
	| ctrl-ncm-B0/36  |                             |                             |                        |                   |
	| ctrl-ncm-B0/37  |                             |                             |                        |                   |
	| ctrl-ncm-B0/38  |                             |                             |                        |                   |
	| ctrl-ncm-B0/39  |                             |                             |                        |                   |
	| ctrl-ncm-B0/40  |                             |                             |                        |                   |
	| ctrl-ncm-B0/41  |                             |                             |                        |                   |
	| ctrl-ncm-B0/42  |                             |                             |                        |                   |
	| ctrl-ncm-B0/43  |                             |                             |                        |                   |
	| ctrl-ncm-B0/44  |                             |                             |                        |                   |
	| ctrl-ncm-B0/45  |                             |                             |                        |                   |
	| ctrl-ncm-B0/46  |                             |                             |                        |                   |
	| ctrl-ncm-B0/47  |                             |                             |                        |                   |
	| ctrl-ncm-B0/48  | ctrl-ncc-0/1                |                             |                        | not-connected     |
	| ctrl-ncm-B0/49  | ctrl-ncc-1/1                | ctrl-ncc-1/1                | ABX                    | ok                |
	| ctrl-ncm-B0/50  |                             |                             |                        |                   |
	| ctrl-ncm-B0/51  | ctrl-ncm-A0/51              | ctrl-ncm-A0/51              | AZ875                  | ok                |
	| ctrl-ncm-B0/52  | ctrl-ncm-A0/52              | ctrl-ncm-A0/52              | AZ875                  | ok                |
	| ctrl-ncm-B0/53  |                             |                             |                        |                   |

	dnRouter# show system backplane fabric

	Fabric Connectivity Statistics:

	NCP-0 : 7/12  (58.8 % of the expected fabric interfaces are connected)
	NCP-1 : 8/12  (66.7 % of the expected fabric interfaces are connected)
	NCP-2 : 10/12 (83.3 % of the expected fabric interfaces are connected)
	NCP-3 : 12/12 (100 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-0:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-0/0/0      | fab-ncf400-0/0/36           | fab-ncf400-0/0/36           | ok                |
	| fab-ncp400-0/0/1      | fab-ncf400-0/0/37           |                             | not-connected     |
	| fab-ncp400-0/0/2      | fab-ncf400-0/0/38           | fab-ncf400-0/0/38           | ok                |
	| fab-ncp400-0/0/3      | fab-ncf400-0/0/39           | fab-ncf400-0/0/40           | error             |
	| fab-ncp400-0/0/4      | fab-ncf400-0/0/40           | fab-ncf400-0/0/39           | error             |
	| fab-ncp400-0/0/5      | fab-ncf400-0/0/41           | fab-ncf400-0/0/41           | ok                |
	| fab-ncp400-0/0/6      | fab-ncf400-0/0/42           | fab-ncf400-0/0/42           | ok                |
	| fab-ncp400-0/0/7      | fab-ncf400-0/0/43           | fab-ncf400-0/0/43           | ok                |
	| fab-ncp400-0/0/8      | fab-ncf400-0/0/44           |                             | not-connected     |
	| fab-ncp400-0/0/9      | fab-ncf400-0/0/45           | fab-ncf400-0/0/45           | ok                |
	| fab-ncp400-0/0/10     | fab-ncf400-0/0/46           |                             | not-connected     |
	| fab-ncp400-0/0/11     | fab-ncf400-0/0/47           | fab-ncf400-0/0/47           | ok                |
	| fab-ncp400-0/0/12     |                             |                             |                   |

	NCP-1:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-1/0/0      | fab-ncf400-0/0/24           | fab-ncf400-0/0/24           | ok                |
	| fab-ncp400-1/0/1      | fab-ncf400-0/0/25           |                             | not-connected     |
	| fab-ncp400-1/0/2      | fab-ncf400-0/0/26           | fab-ncf400-0/0/26           | ok                |
	| fab-ncp400-1/0/3      | fab-ncf400-0/0/27           | fab-ncf400-0/0/28           | error             |
	| fab-ncp400-1/0/4      | fab-ncf400-0/0/28           | fab-ncf400-0/0/27           | error             |
	| fab-ncp400-1/0/5      | fab-ncf400-0/0/29           | fab-ncf400-0/0/29           | ok                |
	| fab-ncp400-1/0/6      | fab-ncf400-0/0/30           | fab-ncf400-0/0/30           | ok                |
	| fab-ncp400-1/0/7      | fab-ncf400-0/0/31           | fab-ncf400-0/0/31           | ok                |
	| fab-ncp400-1/0/8      | fab-ncf400-0/0/32           |                             | not-connected     |
	| fab-ncp400-1/0/9      | fab-ncf400-0/0/33           | fab-ncf400-0/0/33           | ok                |
	| fab-ncp400-1/0/10     | fab-ncf400-0/0/34           | fab-ncf400-0/0/34           | ok                |
	| fab-ncp400-1/0/11     | fab-ncf400-0/0/35           | fab-ncf400-0/0/35           | ok                |
	| fab-ncp400-0/0/12     |                             |                             |                   |

	NCP-2:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-2/0/0      | fab-ncf400-0/0/0            | fab-ncf400-0/0/0            | ok                |
	| fab-ncp400-2/0/1      | fab-ncf400-0/0/1            | fab-ncf400-0/0/1            | ok                |
	| fab-ncp400-2/0/2      | fab-ncf400-0/0/2            | fab-ncf400-0/0/2            | ok                |
	| fab-ncp400-2/0/3      | fab-ncf400-0/0/3            | fab-ncf400-0/0/3            | ok                |
	| fab-ncp400-2/0/4      | fab-ncf400-0/0/4            | fab-ncf400-0/0/4            | ok                |
	| fab-ncp400-2/0/5      | fab-ncf400-0/0/5            | fab-ncf400-0/0/5            | ok                |
	| fab-ncp400-2/0/6      | fab-ncf400-0/0/6            | fab-ncf400-0/0/6            | ok                |
	| fab-ncp400-2/0/7      | fab-ncf400-0/0/7            | fab-ncf400-0/0/7            | ok                |
	| fab-ncp400-2/0/8      | fab-ncf400-0/0/8            | fab-ncf400-0/0/8            | ok                |
	| fab-ncp400-2/0/9      | fab-ncf400-0/0/9            | fab-ncf400-0/0/9            | ok                |
	| fab-ncp400-2/0/10     | fab-ncf400-0/0/10           | fab-ncf400-0/0/10           | ok                |
	| fab-ncp400-2/0/11     | fab-ncf400-0/0/11           |                             | not-connected     |
	| fab-ncp400-2/0/12     |                             | fab-ncf400-0/0/11           | error             |

	NCP-3:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-3/0/0      | fab-ncf400-0/0/12           | fab-ncf400-0/0/12           | ok                |
	| fab-ncp400-3/0/1      | fab-ncf400-0/0/13           | fab-ncf400-0/0/13           | ok                |
	| fab-ncp400-3/0/2      | fab-ncf400-0/0/14           | fab-ncf400-0/0/14           | ok                |
	| fab-ncp400-3/0/3      | fab-ncf400-0/0/15           | fab-ncf400-0/0/15           | ok                |
	| fab-ncp400-3/0/4      | fab-ncf400-0/0/16           | fab-ncf400-0/0/16           | ok                |
	| fab-ncp400-3/0/5      | fab-ncf400-0/0/17           | fab-ncf400-0/0/17           | ok                |
	| fab-ncp400-3/0/6      | fab-ncf400-0/0/18           | fab-ncf400-0/0/18           | ok                |
	| fab-ncp400-3/0/7      | fab-ncf400-0/0/19           | fab-ncf400-0/0/19           | ok                |
	| fab-ncp400-3/0/8      | fab-ncf400-0/0/20           | fab-ncf400-0/0/20           | ok                |
	| fab-ncp400-3/0/9      | fab-ncf400-0/0/21           | fab-ncf400-0/0/21           | ok                |
	| fab-ncp400-3/0/10     | fab-ncf400-0/0/22           | fab-ncf400-0/0/22           | ok                |
	| fab-ncp400-3/0/11     | fab-ncf400-0/0/23           | fab-ncf400-0/0/23           | ok                |
	| fab-ncp400-3/0/12     |                             |                             |                   |


	dnRouter# show system backplane control

	Control Connectivity State:

	NCM-A0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-A0/0   | ipmi-ncf-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/1   |                             |                             |                        |                   |
	| ctrl-ncm-A0/2   |                             |                             |                        |                   |
	| ctrl-ncm-A0/3   |                             |                             |                        |                   |
	| ctrl-ncm-A0/4   | ipmi-ncp-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/5   | ipmi-ncp-2/0                |                             |                        |                   |
	| ctrl-ncm-A0/6   |                             |                             |                        |                   |
	| ctrl-ncm-A0/7   |                             |                             |                        |                   |
	| ctrl-ncm-A0/8   |                             |                             |                        |                   |
	| ctrl-ncm-A0/9   |                             |                             |                        |                   |
	| ctrl-ncm-A0/10  |                             |                             |                        |                   |
	| ctrl-ncm-A0/11  |                             |                             |                        |                   |
	| ctrl-ncm-A0/12  |                             |                             |                        |                   |
	| ctrl-ncm-A0/13  |                             |                             |                        |                   |
	| ctrl-ncm-A0/14  |                             |                             |                        |                   |
	| ctrl-ncm-A0/15  |                             |                             |                        |                   |
	| ctrl-ncm-A0/16  | ctrl-ncf-0/0                | ctrl-ncf-0/0                | 12345                  | ok                |
	| ctrl-ncm-A0/17  | ipmi-ncm-B0/0               |                             |                        |                   |
	| ctrl-ncm-A0/18  |                             |                             |                        |                   |
	| ctrl-ncm-A0/19  |                             |                             |                        |                   |
	| ctrl-ncm-A0/20  |                             |                             |                        |                   |
	| ctrl-ncm-A0/21  |                             |                             |                        |                   |
	| ctrl-ncm-A0/22  |                             |                             |                        |                   |
	| ctrl-ncm-A0/23  |                             |                             |                        |                   |
	| ctrl-ncm-A0/24  | ctrl-ncp-0/0                | ctrl-ncp-0/0                | ABCDE12345             | ok                |
	| ctrl-ncm-A0/25  | ctrl-ncp-1/0                | ctrl-ncp-1/0                | XYZ12345               | ok                |
	| ctrl-ncm-A0/26  | ctrl-ncp-2/0                | ctrl-ncp-x/1                | ABCXYZ                 | error             |
	| ctrl-ncm-A0/27  | ctrl-ncp-3/0                | ctrl-ncp-2/0                | ABCXYZ                 | error             |
	| ctrl-ncm-A0/28  |                             |                             |                        |                   |
	| ctrl-ncm-A0/29  |                             |                             |                        |                   |
	| ctrl-ncm-A0/30  |                             |                             |                        |                   |
	| ctrl-ncm-A0/31  |                             |                             |                        |                   |
	| ctrl-ncm-A0/32  |                             |                             |                        |                   |
	| ctrl-ncm-A0/33  |                             |                             |                        |                   |
	| ctrl-ncm-A0/34  |                             |                             |                        |                   |
	| ctrl-ncm-A0/35  |                             |                             |                        |                   |
	| ctrl-ncm-A0/36  |                             |                             |                        |                   |
	| ctrl-ncm-A0/37  |                             |                             |                        |                   |
	| ctrl-ncm-A0/38  |                             |                             |                        |                   |
	| ctrl-ncm-A0/39  |                             |                             |                        |                   |
	| ctrl-ncm-A0/40  |                             |                             |                        |                   |
	| ctrl-ncm-A0/41  |                             |                             |                        |                   |
	| ctrl-ncm-A0/42  |                             |                             |                        |                   |
	| ctrl-ncm-A0/43  |                             |                             |                        |                   |
	| ctrl-ncm-A0/44  |                             |                             |                        |                   |
	| ctrl-ncm-A0/45  |                             |                             |                        |                   |
	| ctrl-ncm-A0/46  |                             |                             |                        |                   |
	| ctrl-ncm-A0/47  |                             |                             |                        |                   |
	| ctrl-ncm-A0/48  | ctrl-ncc-0/0                |                             |                        | not-connected     |
	| ctrl-ncm-A0/49  | ctrl-ncc-1/0                | ctrl-ncc-1/0                | ABX                    | ok                |
	| ctrl-ncm-A0/50  |                             |                             |                        |                   |
	| ctrl-ncm-A0/51  | ctrl-ncm-B0/51              | ctrl-ncm-B0/51              | AZ876                  | ok                |
	| ctrl-ncm-A0/52  | ctrl-ncm-B0/52              | ctrl-ncm-B0/52              | AZ876                  | ok                |
	| ctrl-ncm-A0/53  |                             |                             |                        |                   |

	NCM-B0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-B0/0   |                             |                             |                        |                   |
	| ctrl-ncm-B0/1   |                             |                             |                        |                   |
	| ctrl-ncm-B0/2   |                             |                             |                        |                   |
	| ctrl-ncm-B0/3   |                             |                             |                        |                   |
	| ctrl-ncm-B0/4   | ipmi-ncp-1/0                |                             |                        |                   |
	| ctrl-ncm-B0/5   | ipmi-ncp-3/0                |                             |                        |                   |
	| ctrl-ncm-B0/6   |                             |                             |                        |                   |
	| ctrl-ncm-B0/7   |                             |                             |                        |                   |
	| ctrl-ncm-B0/8   |                             |                             |                        |                   |
	| ctrl-ncm-B0/9   |                             |                             |                        |                   |
	| ctrl-ncm-B0/10  |                             |                             |                        |                   |
	| ctrl-ncm-B0/11  |                             |                             |                        |                   |
	| ctrl-ncm-B0/12  |                             |                             |                        |                   |
	| ctrl-ncm-B0/13  |                             |                             |                        |                   |
	| ctrl-ncm-B0/14  |                             |                             |                        |                   |
	| ctrl-ncm-B0/15  |                             |                             |                        |                   |
	| ctrl-ncm-B0/16  | ctrl-ncf-0/1                | ctrl-ncf-0/1                | 12345                  | ok                |
	| ctrl-ncm-B0/17  | ipmi-ncm-A0/0               |                             |                        |                   |
	| ctrl-ncm-B0/18  |                             |                             |                        |                   |
	| ctrl-ncm-B0/19  |                             |                             |                        |                   |
	| ctrl-ncm-B0/20  |                             |                             |                        |                   |
	| ctrl-ncm-B0/21  |                             |                             |                        |                   |
	| ctrl-ncm-B0/22  |                             |                             |                        |                   |
	| ctrl-ncm-B0/23  |                             |                             |                        |                   |
	| ctrl-ncm-B0/24  | ctrl-ncp-0/1                | ctrl-ncp-0/1                | ABCDE12345             | ok                |
	| ctrl-ncm-B0/25  | ctrl-ncp-1/1                | ctrl-ncp-1/1                | XYZ12345               | ok                |
	| ctrl-ncm-B0/26  | ctrl-ncp-2/1                | ctrl-ncp-3/1                | ABCXYZ                 | error             |
	| ctrl-ncm-B0/27  | ctrl-ncp-3/1                | ctrl-ncp-2/1                | DBCXYZ                 | error             |
	| ctrl-ncm-B0/28  |                             |                             |                        |                   |
	| ctrl-ncm-B0/29  |                             |                             |                        |                   |
	| ctrl-ncm-B0/30  |                             |                             |                        |                   |
	| ctrl-ncm-B0/31  |                             |                             |                        |                   |
	| ctrl-ncm-B0/32  |                             |                             |                        |                   |
	| ctrl-ncm-B0/33  |                             |                             |                        |                   |
	| ctrl-ncm-B0/34  |                             |                             |                        |                   |
	| ctrl-ncm-B0/35  |                             |                             |                        |                   |
	| ctrl-ncm-B0/36  |                             |                             |                        |                   |
	| ctrl-ncm-B0/37  |                             |                             |                        |                   |
	| ctrl-ncm-B0/38  |                             |                             |                        |                   |
	| ctrl-ncm-B0/39  |                             |                             |                        |                   |
	| ctrl-ncm-B0/40  |                             |                             |                        |                   |
	| ctrl-ncm-B0/41  |                             |                             |                        |                   |
	| ctrl-ncm-B0/42  |                             |                             |                        |                   |
	| ctrl-ncm-B0/43  |                             |                             |                        |                   |
	| ctrl-ncm-B0/44  |                             |                             |                        |                   |
	| ctrl-ncm-B0/45  |                             |                             |                        |                   |
	| ctrl-ncm-B0/46  |                             |                             |                        |                   |
	| ctrl-ncm-B0/47  |                             |                             |                        |                   |
	| ctrl-ncm-B0/48  | ctrl-ncc-0/1                |                             |                        | not-connected     |
	| ctrl-ncm-B0/49  | ctrl-ncc-1/1                | ctrl-ncc-1/1                | ABX                    | ok                |
	| ctrl-ncm-B0/50  |                             |                             |                        |                   |
	| ctrl-ncm-B0/51  | ctrl-ncm-A0/51              | ctrl-ncm-A0/51              | AZ875                  | ok                |
	| ctrl-ncm-B0/52  | ctrl-ncm-A0/52              | ctrl-ncm-A0/52              | AZ875                  | ok                |
	| ctrl-ncm-B0/53  |                             |                             |                        |                   |



	dnRouter# show system backplane fabric ncp 0

	Fabric Connectivity Statistics:

	NCP-0 : 7/12  (58.8 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-0:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-0/0/0      | fab-ncf400-0/0/36           | fab-ncf400-0/0/36           | ok                |
	| fab-ncp400-0/0/1      | fab-ncf400-0/0/37           |                             | not-connected     |
	| fab-ncp400-0/0/2      | fab-ncf400-0/0/38           | fab-ncf400-0/0/38           | ok                |
	| fab-ncp400-0/0/3      | fab-ncf400-0/0/39           | fab-ncf400-0/0/40           | error             |
	| fab-ncp400-0/0/4      | fab-ncf400-0/0/40           | fab-ncf400-0/0/39           | error             |
	| fab-ncp400-0/0/5      | fab-ncf400-0/0/41           | fab-ncf400-0/0/41           | ok                |
	| fab-ncp400-0/0/6      | fab-ncf400-0/0/42           | fab-ncf400-0/0/42           | ok                |
	| fab-ncp400-0/0/7      | fab-ncf400-0/0/43           | fab-ncf400-0/0/43           | ok                |
	| fab-ncp400-0/0/8      | fab-ncf400-0/0/44           |                             | not-connected     |
	| fab-ncp400-0/0/9      | fab-ncf400-0/0/45           | fab-ncf400-0/0/45           | ok                |
	| fab-ncp400-0/0/10     | fab-ncf400-0/0/46           |                             | not-connected     |
	| fab-ncp400-0/0/11     | fab-ncf400-0/0/47           | fab-ncf400-0/0/47           | ok                |
	| fab-ncp400-0/0/12     |                             |                             |                   |



	CLI example (System type CL-96):

	dnRouter# show system backplane

	System Type: CL-96
	Supported element scale: NCC:2, NCF:7, NCP:24, NCM:2

	Fabric Connectivity Statistics:

	NCP-0 :

	NCP-23:

	Fabric Connectivity State:

	NCP-0:

	NCP-23:


	Control Connectivity State:

	NCM-A0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-A0/0   | ipmi-ncf-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/1   | ipmi-ncf-2/0                |                             |                        |                   |
	| ctrl-ncm-A0/2   | ipmi-ncf-4/0                |                             |                        |                   |
	| ctrl-ncm-A0/3   |                             |                             |                        |                   |
	| ctrl-ncm-A0/4   | ipmi-ncp-0/0                |                             |                        |                   |
	| ctrl-ncm-A0/5   | ipmi-ncp-2/0                |                             |                        |                   |
	| ctrl-ncm-A0/6   | ipmi-ncp-4/0                |                             |                        |                   |
	| ctrl-ncm-A0/7   | ipmi-ncp-6/0                |                             |                        |                   |
	| ctrl-ncm-A0/8   | ipmi-ncp-8/0                |                             |                        |                   |
	| ctrl-ncm-A0/9   | ipmi-ncp-10/0               |                             |                        |                   |
	| ctrl-ncm-A0/10  | ipmi-ncp-12/0               |                             |                        |                   |
	| ctrl-ncm-A0/11  | ipmi-ncp-14/0               |                             |                        |                   |
	| ctrl-ncm-A0/12  | ipmi-ncp-16/0               |                             |                        |                   |
	| ctrl-ncm-A0/13  | ipmi-ncp-18/0               |                             |                        |                   |
	| ctrl-ncm-A0/14  | ipmi-ncp-20/0               |                             |                        |                   |
	| ctrl-ncm-A0/15  | ipmi-ncp-22/0               |                             |                        |                   |
	| ctrl-ncm-A0/16  | ctrl-ncf-0/0                | ctrl-ncf-0/0                | 12345                  | ok                |
	| ctrl-ncm-A0/17  | ipmi-ncm-B0/0               |                             |                        |                   |
	| ctrl-ncm-A0/18  | ctrl-ncf-1/0                | ctrl-ncf-1/0                | 22345                  | ok                |
	| ctrl-ncm-A0/19  | ctrl-ncf-2/0                | ctrl-ncf-2/0                | 32345                  | ok                |
	| ctrl-ncm-A0/20  | ctrl-ncf-3/0                | ctrl-ncf-3/0                | 42345                  | ok                |
	| ctrl-ncm-A0/21  | ctrl-ncf-4/0                | ctrl-ncf-4/0                | 52345                  | ok                |
	| ctrl-ncm-A0/22  | ctrl-ncf-5/0                | ctrl-ncf-5/0                | 62345                  | ok                |
	| ctrl-ncm-A0/23  |                             | ctrl-ncf-6/0                | 72345                  |                   |
	| ctrl-ncm-A0/24  | ctrl-ncp-0/0                | ctrl-ncp-0/0                | A2345                  | ok                |
	| ctrl-ncm-A0/25  | ctrl-ncp-1/0                | ctrl-ncp-1/0                | B2345                  | ok                |
	| ctrl-ncm-A0/26  | ctrl-ncp-2/0                | ctrl-ncp-3/0                | C234v                  | error             |
	| ctrl-ncm-A0/27  | ctrl-ncp-3/0                | ctrl-ncp-2/0                | C234c                  | error             |
	| ctrl-ncm-A0/28  | ctrl-ncp-4/0                | ctrl-ncp-4/0                | C2345                  | ok                |
	| ctrl-ncm-A0/29  | ctrl-ncp-5/0                | ctrl-ncp-5/0                | D2345                  | ok                |
	| ctrl-ncm-A0/30  | ctrl-ncp-6/0                | ctrl-ncp-6/0                | E2345                  | ok                |
	| ctrl-ncm-A0/31  | ctrl-ncp-7/0                | ctrl-ncp-7/0                | F2345                  | ok                |
	| ctrl-ncm-A0/32  | ctrl-ncp-8/0                | ctrl-ncp-8/0                | G2345                  | ok                |
	| ctrl-ncm-A0/33  | ctrl-ncp-9/0                | ctrl-ncp-9/0                | H2345                  | ok                |
	| ctrl-ncm-A0/34  | ctrl-ncp-10/0               | ctrl-ncp-10/0               | 123456                 | ok                |
	| ctrl-ncm-A0/35  | ctrl-ncp-11/0               | ctrl-ncp-11/0               | 223456                 | ok                |
	| ctrl-ncm-A0/36  | ctrl-ncp-12/0               | ctrl-ncp-12/0               | 323456                 | ok                |
	| ctrl-ncm-A0/37  | ctrl-ncp-13/0               | ctrl-ncp-13/0               | 423456                 | ok                |
	| ctrl-ncm-A0/38  | ctrl-ncp-14/0               | ctrl-ncp-14/0               | 523456                 | ok                |
	| ctrl-ncm-A0/39  | ctrl-ncp-15/0               | ctrl-ncp-15/0               | 623456                 | ok                |
	| ctrl-ncm-A0/40  | ctrl-ncp-16/0               | ctrl-ncp-16/0               | 723456                 | ok                |
	| ctrl-ncm-A0/41  | ctrl-ncp-17/0               | ctrl-ncp-17/0               | 823456                 | ok                |
	| ctrl-ncm-A0/42  | ctrl-ncp-18/0               | ctrl-ncp-18/0               | 923456                 | ok                |
	| ctrl-ncm-A0/43  | ctrl-ncp-19/0               | ctrl-ncp-19/0               | A23456                 | ok                |
	| ctrl-ncm-A0/44  | ctrl-ncp-20/0               | ctrl-ncp-20/0               | B23456                 | ok                |
	| ctrl-ncm-A0/45  | ctrl-ncp-21/0               | ctrl-ncp-21/0               | N23456                 | ok                |
	| ctrl-ncm-A0/46  | ctrl-ncp-22/0               | ctrl-ncp-22/0               | M23456                 | ok                |
	| ctrl-ncm-A0/47  | ctrl-ncp-23/0               | ctrl-ncp-23/0               | E23456                 | ok                |
	| ctrl-ncm-A0/48  | ctrl-ncc-0/0                |                             |                        | not-connected     |
	| ctrl-ncm-A0/49  | ctrl-ncc-1/0                | ctrl-ncc-1/0                | Ef3456                 | ok                |
	| ctrl-ncm-A0/50  |                             |                             |                        |                   |
	| ctrl-ncm-A0/51  | ctrl-ncm-B0/51              | ctrl-ncm-B0/51              | Ns3456                 | ok                |
	| ctrl-ncm-A0/52  | ctrl-ncm-B0/52              | ctrl-ncm-B0/52              | Ns3456                 | ok                |
	| ctrl-ncm-A0/53  |                             |                             |                        |                   |

	NCM-B0:

	| NCM Interface   | Expected Neighbor Interface | Actual Neighbor Interface   | Actual Neighbor S/N    | Connection State  |
	|-----------------+-----------------------------+-----------------------------+------------------------+-------------------|
	| ctrl-ncm-B0/0   | ipmi-ncf-1/0                |                             |                        |                   |
	| ctrl-ncm-B0/1   | ipmi-ncf-3/0                |                             |                        |                   |
	| ctrl-ncm-B0/2   | ipmi-ncf-5/0                |                             |                        |                   |
	| ctrl-ncm-B0/3   |                             |                             |                        |                   |
	| ctrl-ncm-B0/4   | ipmi-ncp-1/0                |                             |                        |                   |
	| ctrl-ncm-B0/5   | ipmi-ncp-3/0                |                             |                        |                   |
	| ctrl-ncm-B0/6   | ipmi-ncp-5/0                |                             |                        |                   |
	| ctrl-ncm-B0/7   | ipmi-ncp-7/0                |                             |                        |                   |
	| ctrl-ncm-B0/8   | ipmi-ncp-9/0                |                             |                        |                   |
	| ctrl-ncm-B0/9   | ipmi-ncp-11/0               |                             |                        |                   |
	| ctrl-ncm-B0/10  | ipmi-ncp-13/0               |                             |                        |                   |
	| ctrl-ncm-B0/11  | ipmi-ncp-15/0               |                             |                        |                   |
	| ctrl-ncm-B0/12  | ipmi-ncp-17/0               |                             |                        |                   |
	| ctrl-ncm-B0/13  | ipmi-ncp-19/0               |                             |                        |                   |
	| ctrl-ncm-B0/14  | ipmi-ncp-21/0               |                             |                        |                   |
	| ctrl-ncm-B0/15  | ipmi-ncp-23/0               |                             |                        |                   |
	| ctrl-ncm-B0/16  | ctrl-ncf-0/1                | ctrl-ncf-0/1                | 12345                  | ok                |
	| ctrl-ncm-B0/17  | ipmi-ncm-A0/0               |                             |                        |                   |
	| ctrl-ncm-B0/18  | ctrl-ncf-1/1                | ctrl-ncf-1/1                | 22345                  | ok                |
	| ctrl-ncm-B0/19  | ctrl-ncf-2/1                | ctrl-ncf-2/1                | 32345                  | ok                |
	| ctrl-ncm-B0/20  | ctrl-ncf-3/1                | ctrl-ncf-3/1                | 42345                  | ok                |
	| ctrl-ncm-B0/21  | ctrl-ncf-4/1                | ctrl-ncf-4/1                | 52345                  | ok                |
	| ctrl-ncm-B0/22  | ctrl-ncf-5/1                | ctrl-ncf-0/1                | 62345                  | ok                |
	| ctrl-ncm-B0/23  |                             |                             |                        |                   |
	| ctrl-ncm-B0/24  | ctrl-ncp-0/1                | ctrl-ncp-0/1                | A2345                  | ok                |
	| ctrl-ncm-B0/25  | ctrl-ncp-1/1                | ctrl-ncp-1/1                | B2345                  | ok                |
	| ctrl-ncm-B0/26  | ctrl-ncp-2/1                | ctrl-ncp-3/1                | C234v                  | error             |
	| ctrl-ncm-B0/27  | ctrl-ncp-3/1                | ctrl-ncp-2/1                | C234c                  | error             |
	| ctrl-ncm-B0/28  | ctrl-ncp-4/1                | ctrl-ncp-4/1                | C2345                  | ok                |
	| ctrl-ncm-B0/29  | ctrl-ncp-5/1                | ctrl-ncp-5/1                | D2345                  | ok                |
	| ctrl-ncm-B0/30  | ctrl-ncp-6/1                | ctrl-ncp-6/1                | E2345                  | ok                |
	| ctrl-ncm-B0/31  | ctrl-ncp-7/1                | ctrl-ncp-7/1                | F2345                  | ok                |
	| ctrl-ncm-B0/32  | ctrl-ncp-8/1                | ctrl-ncp-8/1                | G2345                  | ok                |
	| ctrl-ncm-B0/33  | ctrl-ncp-9/1                | ctrl-ncp-9/1                | H2345                  | ok                |
	| ctrl-ncm-B0/34  | ctrl-ncp-10/1               | ctrl-ncp-10/1               | 123456                 | ok                |
	| ctrl-ncm-B0/35  | ctrl-ncp-10/1               | ctrl-ncp-11/1               | 223456                 | ok                |
	| ctrl-ncm-B0/36  | ctrl-ncp-12/1               | ctrl-ncp-12/1               | 323456                 | ok                |
	| ctrl-ncm-B0/37  | ctrl-ncp-13/1               | ctrl-ncp-13/1               | 423456                 | ok                |
	| ctrl-ncm-B0/38  | ctrl-ncp-14/1               | ctrl-ncp-14/1               | 523456                 | ok                |
	| ctrl-ncm-B0/39  | ctrl-ncp-15/1               | ctrl-ncp-15/1               | 623456                 | ok                |
	| ctrl-ncm-B0/40  | ctrl-ncp-16/1               | ctrl-ncp-16/1               | 723456                 | ok                |
	| ctrl-ncm-B0/41  | ctrl-ncp-17/1               | ctrl-ncp-17/1               | 823456                 | ok                |
	| ctrl-ncm-B0/42  | ctrl-ncp-18/1               | ctrl-ncp-18/1               | 923456                 | ok                |
	| ctrl-ncm-B0/43  | ctrl-ncp-19/1               | ctrl-ncp-19/1               | A23456                 | ok                |
	| ctrl-ncm-B0/44  | ctrl-ncp-20/1               | ctrl-ncp-20/1               | B23456                 | ok                |
	| ctrl-ncm-B0/45  | ctrl-ncp-21/1               | ctrl-ncp-21/1               | M23456                 | ok                |
	| ctrl-ncm-B0/46  | ctrl-ncp-22/1               | ctrl-ncp-22/1               | N23456                 | ok                |
	| ctrl-ncm-B0/47  | ctrl-ncp-23/1               | ctrl-ncp-23/1               | E23456                 | ok                |
	| ctrl-ncm-B0/48  | ctrl-ncc-0/1                |                             |                        | not-connected     |
	| ctrl-ncm-B0/49  | ctrl-ncc-1/1                | ctrl-ncc-1/0                | Ef3456                 | ok                |
	| ctrl-ncm-B0/50  |                             |                             |                        |                   |
	| ctrl-ncm-B0/51  | ctrl-ncm-A0/51              | ctrl-ncm-A0/51              | Nw3456                 | ok                |
	| ctrl-ncm-B0/52  | ctrl-ncm-A0/52              | ctrl-ncm-A0/52              | Nw3456                 | ok                |
	| ctrl-ncm-B0/53  |                             |                             |                        |                   |


	dnRouter# show system backplane fabric ncp 0

	Fabric Connectivity Statistics:

	NCP-0 : 7/12  (58.3 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-0:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-0/0/0      | fab-ncf400-0/0/0            | fab-ncf400-0/0/0            | ok                |
	| fab-ncp400-0/0/1      | fab-ncf400-1/0/0            |                             | not-connected     |
	| fab-ncp400-0/0/2      | fab-ncf400-2/0/0            | fab-ncf400-2/0/0            | ok                |
	| fab-ncp400-0/0/3      | fab-ncf400-3/0/0            | fab-ncf400-3/0/10           | error             |
	| fab-ncp400-0/0/4      | fab-ncf400-4/0/0            | fab-ncf400-4/0/1            | error             |
	| fab-ncp400-0/0/5      | fab-ncf400-5/0/0            | fab-ncf400-5/0/0            | ok                |
	| fab-ncp400-0/0/6      | fab-ncf400-6/0/0            | fab-ncf400-6/0/0            | ok                |
	| fab-ncp400-0/0/7      | fab-ncf400-0/0/24           | fab-ncf400-0/0/24           | ok                |
	| fab-ncp400-0/0/8      | fab-ncf400-1/0/24           |                             | not-connected     |
	| fab-ncp400-0/0/9      | fab-ncf400-2/0/24           | fab-ncf400-2/0/24           | ok                |
	| fab-ncp400-0/0/10     | fab-ncf400-3/0/24           |                             | not-connected     |
	| fab-ncp400-0/0/11     | fab-ncf400-4/0/24           | fab-ncf400-4/0/24           | ok                |
	| fab-ncp400-0/0/12     |                             | fab-ncf400-5/0/24           |                   |


**Example**
::

	## NC-AI NCP node examples ##
	dnRouter# show system backplane

	System Type: CL-AI-8K-400G (SA-36CD-S-NCP)

	Fabric Connectivity Statistics:

	NCP-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-16:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-16/0/0     | fab-ncf400-0/0/0            | fab-ncf400-0/0/0            | ok                |
	| fab-ncp400-16/0/1     | fab-ncf400-12/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/2     | fab-ncf400-21/0/0           | fab-ncf400-21/0/0           | ok                |
	| fab-ncp400-16/0/3     | fab-ncf400-30/0/0           | fab-ncf400-30/0/10          | error             |
	| fab-ncp400-16/0/4     | fab-ncf400-39/0/0           | fab-ncf400-39/0/1           | error             |
	| fab-ncp400-16/0/5     | fab-ncf400-48/0/0           | fab-ncf400-48/0/0           | ok                |
	| fab-ncp400-16/0/6     | fab-ncf400-57/0/0           | fab-ncf400-57/0/0           | ok                |
	| fab-ncp400-16/0/7     | fab-ncf400-66/0/0           | fab-ncf400-66/0/0           | ok                |
	| fab-ncp400-16/0/8     | fab-ncf400-75/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/9     | fab-ncf400-84/0/0           | fab-ncf400-84/0/0           | ok                |
	| fab-ncp400-16/0/10    | fab-ncf400-93/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/11    | fab-ncf400-102/0/0          | fab-ncf400-102/0/0          | ok                |
	| fab-ncp400-16/0/12    | fab-ncf400-111/0/0          | fab-ncf400-111/0/0          | ok                |
	| fab-ncp400-16/0/13    | fab-ncf400-120/0/0          | fab-ncf400-120/0/0          | ok                |
	| fab-ncp400-16/0/14    | fab-ncf400-129/0/0          | fab-ncf400-129/0/0          | ok                |
	| fab-ncp400-16/0/15    | fab-ncf400-138/0/0          | fab-ncf400-138/0/0          | ok                |
	...
	| fab-ncp400-16/0/35    | fab-ncf400-156/0/0          | fab-ncf400-156/0/0          | ok                |

	dnRouter# show system backplane fabric ncp 16

	Fabric Connectivity Statistics:

	NCP-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-16:

	| NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncp400-16/0/0     | fab-ncf400-0/0/0            | fab-ncf400-0/0/0            | ok                |
	| fab-ncp400-16/0/1     | fab-ncf400-12/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/2     | fab-ncf400-21/0/0           | fab-ncf400-21/0/0           | ok                |
	| fab-ncp400-16/0/3     | fab-ncf400-30/0/0           | fab-ncf400-30/0/10          | error             |
	| fab-ncp400-16/0/4     | fab-ncf400-39/0/0           | fab-ncf400-39/0/1           | error             |
	| fab-ncp400-16/0/5     | fab-ncf400-48/0/0           | fab-ncf400-48/0/0           | ok                |
	| fab-ncp400-16/0/6     | fab-ncf400-57/0/0           | fab-ncf400-57/0/0           | ok                |
	| fab-ncp400-16/0/7     | fab-ncf400-66/0/0           | fab-ncf400-66/0/0           | ok                |
	| fab-ncp400-16/0/8     | fab-ncf400-75/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/9     | fab-ncf400-84/0/0           | fab-ncf400-84/0/0           | ok                |
	| fab-ncp400-16/0/10    | fab-ncf400-93/0/0           |                             | not-connected     |
	| fab-ncp400-16/0/11    | fab-ncf400-102/0/0          | fab-ncf400-102/0/0          | ok                |
	| fab-ncp400-16/0/12    | fab-ncf400-111/0/0          | fab-ncf400-111/0/0          | ok                |
	| fab-ncp400-16/0/13    | fab-ncf400-120/0/0          | fab-ncf400-120/0/0          | ok                |
	| fab-ncp400-16/0/14    | fab-ncf400-129/0/0          | fab-ncf400-129/0/0          | ok                |
	| fab-ncp400-16/0/15    | fab-ncf400-138/0/0          | fab-ncf400-138/0/0          | ok                |
	...
	| fab-ncp400-16/0/35    | fab-ncf400-156/0/0          | fab-ncf400-156/0/0          | ok                |

	dnRouter# show system backplane fabric stats

	Fabric Connectivity Statistics:

	NCP-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	dnRouter# show system backplane fabric stats ncp 16

	Fabric Connectivity Statistics:

	NCP-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	dnRouter# show system backplane fabric ncp 0
		Node ID not supported

**Example**
::

	## NC-AI NCF node examples ##

	dnRouter# show system backplane

	System Type: NCF-0

	Fabric Connectivity Statistics:

	NCF-0 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCF-0:

	| NCF Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncf400-0/0/0      | fab-ncp400-0/0/0            | fab-ncp400-0/0/0            | ok                |
	| fab-ncf400-0/0/1      | fab-ncp400-1/0/0            |                             | not-connected     |
	| fab-ncf400-0/0/2      | fab-ncp400-2/0/0            | fab-ncp400-2/0/0            | ok                |
	| fab-ncf400-0/0/3      | fab-ncp400-3/0/0            | fab-ncf400-30/0/10          | error             |
	| fab-ncf400-0/0/4      | fab-ncp400-4/0/0            | fab-ncf400-39/0/1           | error             |
	...
	| fab-ncf400-0/0/12     | fab-ncf400-396/0/0          | fab-ncf400-396/0/0          | ok                |
	...
	| fab-ncf400-0/0/47     | fab-ncf400-594/0/1          | fab-ncf400-594/0/1          | ok                |
	| fab-ncf400-0/0/24     | fab-ncp400-12/0/0           | fab-ncp400-12/0/0           | ok                |
	...
	| fab-ncf400-0/0/35     | fab-ncp400-23/0/0           | fab-ncp400-23/0/0           | ok                |

	dnRouter# show system backplane fabric ncf 396

	Fabric Connectivity Statistics:

	NCP-396 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	Fabric Connectivity State:

	NCP-396:

	| NCF Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
	|-----------------------+-----------------------------+-----------------------------+-------------------|
	| fab-ncf400-396/0/0    | fab-ncf400-0/0/12           | fab-ncf400-0/0/12           | ok                |
	| fab-ncf400-396/0/1    | fab-ncf400-0/0/13           |                             | not-connected     |
	| fab-ncf400-396/0/2    | fab-ncf400-1/0/12           | fab-ncf400-1/0/12           | ok                |
	| fab-ncf400-396/0/3    | fab-ncf400-1/0/13           | fab-ncf400-10/0/10          | error             |
	| fab-ncf400-396/0/4    | fab-ncf400-36/0/12          | fab-ncf400-36/0/44          | error             |
	| fab-ncf400-396/0/5    | fab-ncf400-36/0/13          | fab-ncf400-36/0/13          | ok                |
	...
	| fab-ncp400-396/0/43   | fab-ncf400-361/0/13         | fab-ncf400-361/0/13         | ok                |

	dnRouter# show system backplane fabric stats

	Fabric Connectivity Statistics:

	NCF-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	dnRouter# show system backplane fabric stats ncf 16

	Fabric Connectivity Statistics:

	NCF-16 : 26/36  (72.2 % of the expected fabric interfaces are connected)

	dnRouter# show system backplane fabric ncf 0
		Node ID not supported

*Example**
::

    dnRouter# show system backplane

    System Type: AI-256-400G-2
    Supported element scale:

    Fabric Connectivity Statistics:

    NCP-0 :

    Fabric Connectivity State:

    NCP-0:


**Example**
::

    dnRouter# show system backplane fabric ncp 1

    Fabric Connectivity Statistics:

    NCP-1 : 26/36  (72.2 % of the expected fabric interfaces are connected)

    Fabric Connectivity State:

    NCP-1:

    | NCP Fabric Interface  | Expected Neighbor Interface | Actual Neighbor Interface   | Connection State  |
    |-----------------------+-----------------------------+-----------------------------+-------------------|
    | fab-ncp400-1/0/0/0    | fab-ncf400-0/0/0/1          | fab-ncf400-0/0/0/1          | ok                |
    | fab-ncp400-1/0/1/0    | fab-ncf400-0/0/1/1          |                             | not-connected     |
    | fab-ncp400-1/0/2/0    | fab-ncf400-0/0/2/1          | fab-ncf400-0/0/2/1          | ok                |
    | fab-ncp400-1/0/3/0    | fab-ncf400-0/0/3/1          | fab-ncf400-0/0/3/0          | error             |
    | fab-ncp400-1/0/4/0    | fab-ncf400-0/0/4/1          | fab-ncf400-0/0/5/0          | error             |
    | fab-ncp400-1/0/5/0    | fab-ncf400-0/0/5/1          | fab-ncf400-0/0/5/1          | ok                |
    | fab-ncp400-1/0/6/0    | fab-ncf400-0/0/6/1          | fab-ncf400-0/0/6/1          | ok                |
    | fab-ncp400-1/0/17/0   | fab-ncf400-0/1/1/1          | fab-ncf400-0/1/1/1          | ok                |
    | fab-ncp400-1/0/0/1    | fab-ncf400-1/0/0/1          |                             | not-connected     |
    | fab-ncp400-1/0/1/1    | fab-ncf400-1/0/1/1          | fab-ncf400-1/0/1/1          | ok                |
    | fab-ncp400-1/0/2/1    | fab-ncf400-1/0/2/1          |                             | not-connected     |
    | fab-ncp400-1/0/3/1    | fab-ncf400-1/0/3/1          | fab-ncf400-1/0/3/1          | ok                |
    | fab-ncp400-1/0/15/1   | fab-ncf400-1/0/15/1         | fab-ncf400-1/0/15/1         | ok                |
    | fab-ncp400-1/0/16/1   | fab-ncf400-1/1/0/1          | fab-ncf400-1/1/0/1          | ok                |
    | fab-ncp400-1/0/17/1   | fab-ncf400-1/1/1/1          | fab-ncf400-1/1/1/1          | ok                |


dnRouter# show system backplane fabric stats

    Fabric Connectivity Statistics:

    NCP-0 : 26/36  (72.2 % of the expected fabric interfaces are connected)

    dnRouter# show system backplane fabric stats ncp 0

    Fabric Connectivity Statistics:

    NCP-0 : 26/36  (72.2 % of the expected fabric interfaces are connected)

.. **Help line:** show system backplane

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 5.1.0   | Command introduced                                |
+---------+---------------------------------------------------+
| 10.0    | Command not supported                             |
+---------+---------------------------------------------------+
| 11.0    | Command reintroduced with Network Cloud Elements. |
+---------+---------------------------------------------------+
| 15.1    | Added support for new cluster types               |
+---------+---------------------------------------------------+
| 16.1    | Added support for CL-51 and CL-76 cluster types   |
+---------+---------------------------------------------------+
| 17.2    | Added support for CL-49 and CL-86 cluster types   |
+---------+---------------------------------------------------+
| 18.1    | Added support for CL-153 cluster type             |
+---------+---------------------------------------------------+
| 19.10   | Added support for AI-768-400G-1 cluster type      |
+---------+---------------------------------------------------+
