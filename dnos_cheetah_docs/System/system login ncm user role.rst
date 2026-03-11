system login ncm user role
--------------------------

**Minimum user role:** operator

To configure the user's role:

**Command syntax: role [role]**

**Command mode:** config

**Hierarchies**

- system login ncm user


.. **Note**

	The following roles exist by default:

	-  admin - has full control

	-  viewer - able to use "show" commands only

	**Validation:**

	- only DNOS admin and techsupport role users can define roles of ncm users

	- It is not possible to configure new ncm roles

**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                                                                                                       | Range       | Default |
+===========+===================================================================================================================================================+=============+=========+
| role      | Enter admin/operator/viewer (lowercase). The default is "viewer". If you do not assign a role, the user will be assigned the default viewer role. | techsupport | viewer  |
|           |                                                                                                                                                   | admin       |         |
|           |                                                                                                                                                   | operator    |         |
|           |                                                                                                                                                   | viewer      |         |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+-------------+---------+

Roles are used for authorization. After a user is authenticated, the user is granted access depending on his/her assigned role.

The available roles are:

- Techsupport - has full control

- Admin - has full control

- Operator - has full control, except request system restart commands

- Viewer - can execute show commands only

The minimum user role required for each command is specified for every command in this manual, as follows:

The minimum user role required for this command:

+--------------+----------------------------------------------------------------------+
| User Role    | Description                                                          |
+==============+======================================================================+
| Techsupport  | Only Techsupport can execute the command.                            |
+--------------+----------------------------------------------------------------------+
| Admin        | Administrators and Techsupport can execute the command.              |
+--------------+----------------------------------------------------------------------+
| Operator     | Operators, Administrators, and Techsupport can execute the command.  |
+--------------+----------------------------------------------------------------------+
| Viewer       | Viewers, Operators, and Administrators can execute the command.      |
+--------------+----------------------------------------------------------------------+

- Only DNOS techsupport users can create an NCM techsupport user

- Only users with admin or techsupport roles can change roles of existing users

- A user with an admin role cannot change the role of a user with a techsupport role

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1
	dnRouter(system-login-ncm-user1)# role admin



.. **Help line:** Configure ncm user role

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+


