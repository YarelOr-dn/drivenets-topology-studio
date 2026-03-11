system ssh server vrf client-list type
--------------------------------------

**Minimum user role:** operator

This command defines whether the configured client-list (see system ssh server vrf client-list) is a white list or a black list. This will determine if the listed clients will be granted access to the in-band SSH server.

**Command syntax: server vrf client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Note**

- If the list-type is set to "allow", the client list must not be empty.

.. - no command return the list type to its default value

	- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+-----------+--------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                          | Range | Default |
+===========+======================================================================================+=======+=========+
| list-type | Defines whether the listed clients will be granted access to the in-band SSH server. | allow | deny    |
|           |                                                                                      | deny  |         |
+-----------+--------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ssh 
	dnRouter(cfg-system-ssh)# server vrf default
	dnRouter(cfg-ssh-server-vrf)# client-list type allow
	
	
	

**Removing Configuration**

To revert the type to default:
::

	dnRouter(cfg-ssh-server-vrf)# no client-list type

.. **Help line:** configure black or white list of incoming IP-addresses per vrf for ssh server.

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 6.0     | Command introduced            |
+---------+-------------------------------+
| 10.0    | Merged with system ssh server |
+---------+-------------------------------+
| 11.0    | Moved into system ssh server  |
+---------+-------------------------------+
| 13.1    | Moved under VRF hierarchy     |
+---------+-------------------------------+

