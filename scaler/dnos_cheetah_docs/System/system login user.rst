system login user 
------------------

**Minimum user role:** operator

You can configure users locally and/or on a TACACS+.RADIUS server. If both local and remote authentication types are set, local authentication, via a password stored on the device, will be used only if the authentication from the TACACS+ or RADIUS authentication server is not available or fails.

The following sections describe how to configure users locally using the DNOS CLI. For instructions on configuring users on the TACACS+.RADIUS server, refer to the TACACS+/RADIUS documentation.

The following default users are mandatory:

- dnroot - with role admin - the default password can only be changed by users with "admin" or "techsupport" roles

- dntechsupport - with role techsupport - the default password can only be changed by users with "techsupport" role

- Users with "techsupport" role can only be created, changed, or deleted by other users with a "techsupport" role

To create a local user and/or enter a user's configuration mode:

**Command syntax: user [user-name]**

**Command mode:** config

**Hierarchies**

- system login


**Note**

- Notice the change in prompt.

- Default local users cannot be deleted or changed.

.. - If user name does not exist, new user is created

	- no command removes the user configuration. By default new user name get "Viewer" role.

	- User must be configured with a password or with an SSH key or with both, otherwise commit will fail.

	- The following default users should exist:

	- dnroot - role admin

	- dntechsupport - role techsupport

	- default local users cannot be deleted

	- default local users role cannot be changed

	- techsupport role user can only be created/changed/deleted by techsupport

	- admin/operator/viewer role users can only be created/changed deleted by admin/techsupport users

	- default local users password can ONLY be changed according to the following-rules

	- dnroot - can be changed by admin/techsupport

	- dntechsupport - can be changed by techsupport

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                                               |
+===========+===========================================================================================================================================================================+
| user-name | The user identifier. This is a mandatory parameter and it must be unique in the system. The user name must have a minimum of 2 characters and a maximum of 20 characters. |
|           | Allowed characters: a-z, A-Z, 0-9, - (hyphen), _ (underscore), ~ (tilda)                                                                                                  |
|           | The first character must be a letter, a-z or A-Z.                                                                                                                         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

If the user name does not exist, it will be created.

The user must be configured with a password or with an SSH key, or with both. If it isn't, the commit will fail. See system login user password.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)#
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no user MyUserName

.. **Help line:** Configure login user name

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                          |
+---------+----------------------------------------------------------------+
| 10.0    | Added limitations on creating/updating users depending on role |
|         | Applied new user hierarchy                                     |
+---------+----------------------------------------------------------------+


