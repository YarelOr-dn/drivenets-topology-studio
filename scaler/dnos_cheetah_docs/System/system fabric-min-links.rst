system fabric-min-links
-----------------------

**Minimum user role:** operator

Each NCP in the cluster is connected to the NCF using up to 40 links depending on the NCP model and cluster type. You can configure the minimum number of NCP fabric member interfaces that must be active for the NCP to be available. The configuration is global for all NCPs in the cluster.

For non-blocking traffic, we recommend configuring a minimum of 11 fabric links for small clusters, 10 fabric links for medium and large clusters (the number of physical fabric interface connections minus 1), and 32 fabric links for clusters using NCP-36CD-S model types, which is the minimum number of NCP fabric member interfaces that must be active for the NCP-36CD-S model type to be available.

If you receive the system event IF_LINK_STATE_CHANGE_MIN_LINKS_REACHED, the link state has moved to a 'down' state because the configured min-links limit has been reached. To correct this, check the faulty links and the NCF or use the system fabric-min-links configuration command to reconfigure the minimum number of required NCF links.

To configure the number of fabric links that must be active:

**Command syntax: fabric-min-links [fabric-min-links]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- This command is not applicable to a standalone NCP.

.. - This configuration applies to system cluster types, for standalone SA-40C, configuration is not available.

	- Validation – number of fabric-min-links cannot be higher than supported fabric interfaces per ncp in cluster (per cluster type)

	- no command restores the fabric min-links value to default value

**Parameter table**

+------------------+------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                  | Range | Default |
+==================+==============================================================================+=======+=========+
| fabric-min-links | The number of links below which the NCP will become unavailable.             | 0..40 | 1       |
|                  | The value cannot be higher than supported fabric interfaces per cluster NCP. |       |         |
+------------------+------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# fabric-min-links 11

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system)# no fabric-min-links

.. **Help line:** configures fabric min-links value per NCP

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 11.5    | Changed the default value to 10  |
+---------+----------------------------------+
| 13.3    | Changed the default from 10 to 1 |
+---------+----------------------------------+
| 16.1    | Extended upper bound to 40 links |
+---------+----------------------------------+
| 19.10   | Added setting of 0 for AI nodes  |
+---------+----------------------------------+
