system tcp path-mtu-discovery tcp-probing admin-state
-----------------------------------------------------

**Minimum user role:** operator

Enable/disable packet-layer path-mtu-discovery probing for "from-us" control protocols that run over TCP (as per RFC4821).

To enable/disable the configuration per packet-layer path-mtu-discovery probing:

**Command syntax: tcp path-mtu-discovery tcp-probing admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system tcp path-mtu-discovery tcp-probing

**Note**

- Notice the change in prompt.

.. - No command returns the state to default.

**Parameter table**

+----------------+-------------------------------------------------------------+-------------+------------+
|                |                                                             |             |            |
| Parameter      | Description                                                 | Range       | Default    |
+================+=============================================================+=============+============+
|                |                                                             |             |            |
| admin-state    | Enable/disable packet-layer   path-mtu-discovery probing    | Enabled     | Enabled    |
|                |                                                             |             |            |
|                |                                                             | Disabled    |            |
+----------------+-------------------------------------------------------------+-------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	dnRouter(cfg-system-tcp)# path-mtu-discovery
	dnRouter(cfg-system-tcp-pmtud)# tcp-probing
	dnRouter(cfg-tcp-pmtud-probing)# admin-state disabled


**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-tcp-pmtud-probing)# no admin-state

.. **Help line:** enable/disable PL-PMTUD probing for "from-us" control protocols over TCP as per RFC4821.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
