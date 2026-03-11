system login ipmi user 
-----------------------

**Minimum user role:** operator

To configure credentials for DNOS ipmi interfaces.

**Command syntax: ipmi user [user-name]**

**Command mode:** config

**Hierarchies**

- system login ipmi


**Note**

- Notice the change in prompt

- If the user-name does not exist, a new user will be created.

.. - If user name does not exist, new user is created

	- The following default users should exist:

	   - dnroot - privilege administrator

	- "no ipmi" command sets the values to default

	- "no users" removes all user-names for IPMI except "dnroot"

	- "no user <user-name> remove specific user-name for IPMI

	- typed password is not presented to the user


	**Validation:**

	- default local user cannot be deleted

	- default local user privilege cannot be changed

	- administrator users IPMI users can only be created/changed deleted by admin/techsupport users

	- default local users password can ONLY be changed according to the following-rules

	   - dnroot - can be changed by admin/techsupport

	- User must configured with a password, if user has been configured without password, commit will fail

**Parameter table**

+-----------+---------------------------------------------------------+--------+
| Parameter | Description                                             | Range  |
+===========+=========================================================+========+
| user-name | Enter a user-name for accessing the DNOS IPMI interface | String |
+-----------+---------------------------------------------------------+--------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)#
	

	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-login-ipmi)# no user user1
	dnRouter(cfg-system-login-ipmi)# no user
	dnRouter(cfg-system-login)# no ipmi

.. **Help line:** configure credentials for DNOS ipmi interfaces.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


