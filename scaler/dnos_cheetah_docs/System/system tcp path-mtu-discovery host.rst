system tcp path-mtu-discovery host
-----------------------------------------------

**Minimum user role:** operator

Configure the path-mtu-discovery for "from-us" control protocols that run over TCP.

To configure the path-mtu-discovery host:

**Command syntax: tcp path-mtu-discovery host**

**Command mode:** config

**Hierarchies**

-  system tcp path-mtu-discovery

**Note**

- Notice the change in prompt.

.. - No command returns the all path-mtu-discovery host configurations to default.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	dnRouter(cfg-system-tcp)# path-mtu-discovery
	dnRouter(cfg-system-tcp-pmtud)# host
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-tcp-pmtud)# no host

.. **Help line:** configuration per path-mtu-discovery for "from-us" control protocols that runs over TCP

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


