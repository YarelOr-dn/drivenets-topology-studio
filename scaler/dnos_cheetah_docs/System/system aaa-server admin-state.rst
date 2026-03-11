system aaa-server admin-state
-----------------------------

**Minimum user role:** admin

You can use this command to configure the admin state of remote AAA. To enable the aaa-server:

**Command syntax: admin-state [state]**

**Command mode:** config

**Hierarchies**

- system aaa-server

.. **Note**

.. No command set default admin-state value.

**Parameter table**

+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+---------+
| Parameter   | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Range    | Default |
+=============+====================================================================================================================================================================================================================================================================================================================================================================================================================================================================================+==========+=========+
| admin-state | Configure the admin state of remote AAA. If aaa-server admin-state is enabled, each AAA request will be sent to one of the AAA servers enabled for the required AAA function. Servers can be separately enabled or disabled for each one of the three AAA functions. If no AAA server is enabled for one of the functions, no AAA requests will be sent at all, and local users will be used for login. If aaa-server admin-state is disabled, local users will be used for login. | Enabled  | Enabled |
|             |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Disabled |         |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# admin-state enabled
	dnRouter(cfg-system-aaa)# admin-state disabled
	

**Removing Configuration**

To revert to the default admin-state:
::

	dnRouter(cfg-system-aaa)# no admin-state

.. **Help line:** Set the bgp router-id

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 6.0     | Command introduced                        |
+---------+-------------------------------------------+
| 11.2    | Admin-state default changed to "enabled". |
+---------+-------------------------------------------+

