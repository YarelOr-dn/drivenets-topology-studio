system telnet server vrf client-list type
-----------------------------------------

**Minimum user role:** operator

This command defines whether the configured client-list (see system telnet server vrf client-list) is a white list or a black list. This will determine if the listed clients will be granted access to the system in-band telnet server.

**Command syntax: server vrf client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system telnet server 

**Note**

- If client-list type is set to "allow", the client-list must not be empty.

.. - no command return the list type to its default value

	- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+-----------+-------------------------------------------+-------+---------+
| Parameter | Description                               | Range | Default |
+===========+===========================================+=======+=========+
| list-type | The type of list of incoming IP addresses | allow | deny    |
|           |                                           | deny  |         |
+-----------+-------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# telnet 
	dnRouter(cfg-system-telnet)# server vrf default
	dnRouter(cfg-telnet-server-vrf)# client-list type allow
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-telnet-server-vrf)# no client-list type

.. **Help line:** configure black or white list of incoming IP-addresses for system in-band telnet server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


