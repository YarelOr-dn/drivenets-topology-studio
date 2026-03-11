system ftp server
-----------------

**Minimum user role:** operator

Use the following command to configure FTP server parameters:

**Command syntax: server [parameters]**

**Command mode:** config

**Hierarchies**

- system ftp

**Note**

- Notice the change in prompt

**Parameter table**

+-------------------------+-------------------------------------------------------+---------------------+---------+
| Parameter               | Description                                           | Range               | Default |
+=========================+=======================================================+=====================+=========+
| admin-state             | Set the administrative state of the FTP server        | enabled             | enabled |
|                         |                                                       | disabled            |         |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| class-of-service        | Configure the system class-of-service for FTP packets | 0..56               | 16      |
|                         | (the value is the DSCP value on the IP header)        |                     |         |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| client-list             | The IPv4 and IPv6 addresses for system FTP server     | A.B.C.D/x           | \-      |
| server                  |                                                       | IPv6-address-format |         |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| data-connection-timeout | Configure the timeout (in minutes)                    | 0..90               | 5       |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| idle-session-timeout    | Configure the timeout (in minutes)                    | 0..90               | 30      |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| list-type               | The type of list                                      | allow               | deny    |
|                         |                                                       | deny                |         |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| max-sessions            | The maximum number of allowed FTP sessions            | 1..32               | 10      |
+-------------------------+-------------------------------------------------------+---------------------+---------+
| vrf-name                | The name of the VRF                                   | default             | \-      |
|                         |                                                       | mgmt0               |         |
+-------------------------+-------------------------------------------------------+---------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ftp
	dnRouter(cfg-system-ftp)# server
	dnRouter(cfg-system-ftp-server)#
	


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ftp-server)# no ftp server

.. **Help line:** configure ftp server parameters.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+



