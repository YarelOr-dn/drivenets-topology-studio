system aaa-server radius server authentication
----------------------------------------------

**Minimum user role:** admin

You need to enable the RADIUS server to use it for authentication. If no server is enabled for authentication, local users will be used for login authentication.

To enable/disable the RADIUS authentication server:

**Command syntax: authentication [admin-state]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server

**Note**

- RADIUS and TACACS+ authentication servers may not be enabled simultaneously.

.. - 'no' command sets default admin-state value.

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                     | Range    | Default  |
+=============+=================================================================================================================================+==========+==========+
| admin-state | The administrative state of the RADIUS authentication server. When enabled, authentication requests may be sent to this server. | Enabled  | Disabled |
|             |                                                                                                                                 | Disabled |          |
+-------------+---------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
	dnRouter(cfg-aaa-radius-server)# authentication enabled




**Removing Configuration**

To revert the admin-state to the default value:
::

	dnRouter(cfg-aaa-radius-server)# no authentication

.. **Help line:** Enable/disable authentication on this server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
