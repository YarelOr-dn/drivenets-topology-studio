system login techsupport-login
------------------------------

**Minimum user role:** operator

To allow or deny login access to users with a techsupport role:

**Command syntax: techsupport-login admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system login 


.. **Note**

	- no command sets the values to default

**Parameter table**

+-------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+
| Parameter   | Description                                                                                                                                                         | Range    | Default  |
+=============+=====================================================================================================================================================================+==========+==========+
| admin-state | The administrative state of the techsupport login. When enabled, login access will be granted to users with a "techsupport" role. Otherwise, access will be denied. | Enabled  | Disabled |
|             |                                                                                                                                                                     | Disabled |          |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# techsupport-login admin-state enabled
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no techsupport-login

.. **Help line:** allow or deny login for users with techsupport role.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


