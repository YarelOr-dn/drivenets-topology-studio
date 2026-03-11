system login 
-------------

**Minimum user role:** operator

From the system login hierarchy you can configure new users and login parameters.

To enter system login configuration mode:

**Command syntax: login [parameters]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- You may only create/update parameters of users with an equivalent or lower role level. For example, users with a "techsupport" role can only be created or changed by users with a "techsupport" role; users with an "operator" role can only create or change users with "viewer" or "operator" roles; etc.

- Notice the change in prompt

.. - Validation: user must be configured with a password

	- It is not possible to remove password configuration

	- no command removes the user configuration


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# banner This is My banner
	dnRouter(cfg-system-login)# user MyUserName 
	dnRouter(cfg-system-login-MyUserName)#
	

	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login)# no user MyUserName
	dnRouter(cfg-system-login)# no banner

.. **Help line:** Configure system login users

**Command History**

+---------+---------------------------------------------+
| Release | Modification                                |
+=========+=============================================+
| 6.0     | Command introduced as part of new hierarchy |
+---------+---------------------------------------------+


