system login ncm user 
---------------------

**Minimum user role:** operator

You need a user name and a password to access the NCM. Using this command, you can configure users and passwords directly from the DNOS CLI. When the NCM connects to the cluster, it will synchronize with the allowed users.

You need an admin/techsupport privileges to create or change a user with an admin role.

You need an techsupport privileges to create or change a user with a techsupport role.

To configure a user:

**Command syntax: ncm user [user-name]**

**Command mode:** config

**Hierarchies**

- system login

**Note**

- Notice the change in prompt

.. - If user name does not exist, new user is created

	- The following default users should exist:

	- dnrootncm - privilege administrator

	- "no user <user-name> remove specific user-name from NCM

	- typed password is not presented to the user


	**Validation:**

	- default user cannot be deleted

	- default user privilege cannot be changed

	- "admin" will not be an available user-name - operator which will type "admin" will get an error message "unsupported user name"

	- admin/viewer role users can only be created/changed deleted by DNOS admin/techsupport users

	- default users password can ONLY be changed according to the following-rules

	- dnrootncm - can be changed by DNOS admin/techsupport user

	- User must configured with a password, if user has been configured without password, commit will fail

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                                                                                       | Range  | Default |
+===========+===================================================================================================================================================+========+=========+
| user-name | Enter a user-name for accessing the NCM console. If the name doesn't already exist, it will be created and you will enter its configuration mode. | String | \-      |
|           | You cannot configure a user named "admin".                                                                                                        |        |         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1
	dnRouter(system-login-ncm-user1)#
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-ncm)# no user user1

.. **Help line:** configure credentials for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+

