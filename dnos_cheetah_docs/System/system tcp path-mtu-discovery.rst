system tcp path-mtu-discovery
-----------------------------------------------

**Minimum user role:** operator

Configure the maximum transmission unit (MTU) size on a network path between two IPs.

To configure the path-mtu-discovery:

**Command syntax: tcp path-mtu-discovery**

**Command mode:** config

**Hierarchies**

- system tcp 

**Note**

- Notice the change in prompt.

.. - No command returns the all path-mtu-discovery configurations to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	dnRouter(cfg-system-tcp)# path-mtu-discovery
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-tcp)# no path-mtu-discovery

.. **Help line:** configuration per path-mtu-discovery feature.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


