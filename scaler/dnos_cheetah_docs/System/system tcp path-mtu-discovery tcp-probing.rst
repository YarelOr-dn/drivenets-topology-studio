system tcp path-mtu-discovery tcp-probing
-----------------------------------------------

**Minimum user role:** operator

Configuration per packet-layer path-mtu-discovery for "from-us" control protocols that run over TCP.

To configure the per packet-layer path-mtu-discovery:

**Command syntax: tcp path-mtu-discovery tcp-probing**

**Command mode:** config

**Hierarchies**

- system tcp path-mtu-discovery

**Note**

- Notice the change in prompt.

.. - No command returns the all path-mtu-discovery tcp-probing configurations to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	dnRouter(cfg-system-tcp)# path-mtu-discovery
	dnRouter(cfg-system-tcp-pmtud)# tcp-probing
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-tcp-pmtud)# no tcp-probing

.. **Help line:** configuration per packet-layer-path-mtu-discovery for "from-us" control-protocols over TCP..

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


