system aaa-server radius server authorization
---------------------------------------------

**Minimum user role:** admin

To configure the admin state of authorization using the RADIUS server:

**Command syntax: authorization [admin-state]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server


**Note**

- Notice the change in prompt.

- Validation: RADIUS authorization allowed to be enabled only if RADIUS authentication is enabled.

.. - 'no' command sets default admin-state value.

**Parameter table**

+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                                                | Range    | Default  |
+=============+============================================================================================================================================================+==========+==========+
| admin-state | Enable/disable authorization on this server. If enabled, authorization requests may be sent to this server.                                                | enabled  | disabled |
|             | If disabled, authorization requests will not be sent to this server. If no RADIUS server is enabled for authorization, local users will be used for login. | disabled |          |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# server priority 3 address 192.168.1.3
	dnRouter(cfg-aaa-radius-server)# authorization enabled
	


**Removing Configuration**

To revert the authorization to default:
::

	dnRouter(system-aaa-radius-server)# no authorization

.. **Help line:** Enable/disable authorization on this server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
