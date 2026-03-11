system login user role
----------------------

**Minimum user role:** operator

Only users with admin or techsupport role can change roles of existing users. Users with an admin role cannot change the role of a user with a techsupport role.

More complex profiles can be set by combining roles with groups in the TACACS+ server. For more details, see system aaa-server.

Local users can only be configured with Admin, Operator, or Viewer roles. It is not possible to create new local roles.

To assign a role to a local user:

**Command syntax: user [user-name]** role [role]

**Command mode:** config

**Hierarchies**

- system login


.. **Note**

	- no command reverts the role to its default value

	The following roles exist by default:

	- admin - has full control

	- operator - has full control with several exceptions

	- viewer - able to use "show" commands only

	- If user name does not exist, new user is created

	**Validation:**

	- only admin and techsupport role users can change roles of existing users

	- user with role admin, cannot change role of techsupport role user

	- TACACS can be configured with any of the default system roles.

	- Local users can be configured only with admin/operator/viewer. It is not possible to configure new local roles


**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                       |
+===========+===================================================================================================================================================+
| role      | Enter admin/operator/viewer (lowercase). The default is "viewer". If you do not assign a role, the user will be assigned the default viewer role. |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------+

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

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName 
	dnRouter(cfg-system-login-MyUserName)# role admin
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-MyUserName)# no role

.. **Help line:** Configure user role

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 10.0    | Applied new hierarchy |
+---------+-----------------------+


