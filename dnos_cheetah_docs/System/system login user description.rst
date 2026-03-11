system login user description
-----------------------------

**Minimum user role:** operator

To set an optional description for the user:

**Command syntax: user [user-name]** description [description]

**Command mode:** config

**Hierarchies**

- system login


**Note**

- A techsupport role cannot change the description of a user with an admin role.

.. - no command removes the user description

	- If user name does not exist, new user is created

	**Validation:**

	- only users with role admin/techsupport, can edit other local users

	- user with role admin, cannot edited by user with techsupport role

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------+
| Parameter   | Description                                                                                                                            |
+=============+========================================================================================================================================+
| description | Provide a description for the user.                                                                                                    |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example: |
|             | ... description "My long description"                                                                                                  |
|             | ... description My_long_description                                                                                                    |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# description MyDescription

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName)# no description

.. **Help line:** Configure login user description

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


