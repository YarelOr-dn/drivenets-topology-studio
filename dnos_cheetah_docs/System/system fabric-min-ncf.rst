system fabric-min-ncf
-----------------------

**Minimum user role:** operator

Every cluster has a recommended number of cluster NCFs that takes into consideration N+1 redundancy:

- Small cluster: 1 NCF (no redundancy)

- Medium cluster: 6 NCFs (5+1)

- Large cluster: 11 NCFs (10+1)

For non-blocking traffic, we recommend configuring the following number of minimum NCFs:

- 1 - for CL-32 using NCP-40C model types. Available range 1-2.

- 2 - for CL-48 using NCP-40C model types. Available range 1-3.

- 3 - for CL-49 using NCP-64X12C-S and NCP-40C and NCP-10CD model types. Available range 1-3.

- 3 - for CL-51 using NCP-36CD-S model types. Available range 1-3.

- 3 - for CL-64 using NCP-40C model types. Available range 1-4.

- 4 - for CL-76 using NCP-36CD-S model types. Available range 1-5.

- 5 - for CL-86 using NCP-64X12C-S and NCP-40C and NCP-10CD model types. Available range 1-6.

- 5 - for CL-96 using NCP-40C model types. Available range 1-7.

- 8 - for CL-153 using NCP-36CD-S model types. Available range 1-10.

- 10 - for CL-192 using NCP-40C model types. Available range 1-13.

- 32 - for CL-409 using NCP-36CD-S model types. Available range 1-36.

- 18 - for AI-768-400G-1 using NCP-36CD-S model types. Available range 0-20.

- 2  - for AI-256-400G-2 using NCP-38E model types. Available range 0-2.

- 32 - for AI-8192-400G-2 using NCP-38E model types. Available range 0-36.

- 1  - for AI-72-800G-2 using NCP-38E model types. Available range 0-1.

To configure the minimum number of NCF nodes that must be active for all the NCPs in the cluster to be active:

**Command syntax: fabric-min-ncf [fabric-min-ncf]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- This command is not applicable to a standalone NCP.

.. - no command restores the fabric-min-ncf value to default value

	- This configuration applies to system cluster types, for standalone, configuration is not available.

	- Validation – number of fabric-min-ncf cannot be higher than supported ncfs in cluster (per cluster type)

**Parameter table**

+----------------+--------------------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                                          | Range | Default |
+================+======================================================================================+=======+=========+
| fabric-min-ncf | The number of active NCF nodes below which the cluster NCPs will become unavailable. | 0..36 | 1       |
|                | The value cannot be higher than the number of supported NCFs in the cluster.         |       |         |
+----------------+--------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# fabric-min-ncf 10

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system)# no fabric-min-ncf

.. **Help line:** configures minimum ncf

**Command History**

+---------+------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                         |
+=========+======================================================================================================+
| 11.2    | Command introduced                                                                                   |
+---------+------------------------------------------------------------------------------------------------------+
| 13.3    | Changed the defaults from 6 for medium cluster and 11 for large clusters to 1 for both cluster types |
+---------+------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for CL-32, CL-48, and CL-64                                                            |
+---------+------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for CL-51 and CL-76                                                                    |
+---------+------------------------------------------------------------------------------------------------------+
| 18.1    | Added support for CL-153                                                                             |
+---------+------------------------------------------------------------------------------------------------------+
| 19.10   | Added support for AI cluster formations                                                              |
+---------+------------------------------------------------------------------------------------------------------+
