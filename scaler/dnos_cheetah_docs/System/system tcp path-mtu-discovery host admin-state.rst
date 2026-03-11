system tcp path-mtu-discovery host admin-state
-----------------------------------------------

**Minimum user role:** operator

Administratively enable/disable the path-mtu-discovery for "from-us" control protocols that run over TCP..

**Command syntax: tcp path-mtu-discovery host admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system tcp path-mtu-discovery host

**Note**

- Notice the change in prompt.

.. -  No command returns the state to default.

**Parameter table**

+-------------+-----------------------------------------------+----------+---------+
| Parameter   | Description                                   | Range    | Default |
+=============+===============================================+==========+=========+
| admin-state | Configure the state of the path-mtu-discovery | enabled  | enabled |
|             |                                               | disabled |         |
+-------------+-----------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# tcp
	dnRouter(cfg-system-tcp)# path-mtu-discovery
	dnRouter(cfg-system-tcp-pmtud)# host
	dnRouter(system-tcp-pmtud-host)# admin-state disabled
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(system-tcp-pmtud-host)# no admin-state

.. **Help line:** enable/disable path-mtu-discovery for "from-us" control protocols that runs over TCP

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+


