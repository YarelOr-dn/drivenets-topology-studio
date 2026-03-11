system ftp server vrf client-list type
--------------------------------------

**Minimum user role:** operator

Use the following command to configure the black or white list of incoming IP addresses per VRF for ftp server:

**Command syntax: server vrf client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system ftp server vrf


**Note**

- If the client-list type is set to 'allow', the client-list must not be empty.

- The 'no client-list type' returns the list type to its default value.

.. - no command return the list type to its default value

	- if client-list type is set to "allow", client-list must not be empty

**Parameter table**

+-----------+--------------------------------------------+-------+---------+
| Parameter | Description                                | Range | Default |
+===========+============================================+=======+=========+
| list-type | The type of list for incoming IP addresses | allow | deny    |
|           |                                            | deny  |         |
+-----------+--------------------------------------------+-------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server vrf default
	dnRouter(cfg-system-ftp-server)# client-list type allow




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-ftp-server)# no client-list type

.. **Help line:** configure black or white list of incoming IP-addresses per VRF for ftp server.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
