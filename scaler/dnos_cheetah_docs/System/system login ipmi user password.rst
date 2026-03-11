system login ipmi user password 
-------------------------------

**Minimum user role:** operator

To configure an encrypted password for DNOS ipmi interfaces.

**Command syntax: password** [password]

**Command mode:** config

**Hierarchies**

- system login ipmi


**Note**

- This command may also be used to change the password for existing users. Typically, when you want to create a new user with a new password, you would use the clear password option.

- You need an admin or techsupport role to change the password for dnroot.

.. - One line command allows to enter password in encrypted format only.

	- It is not possible to remove password

	- If password with no value is entered, clear text password is requested with double confirmation. Clear password size is limited by 16 characters

	**Validation:**

	- only user with admin/techsupport role can edit passwords for users with privilege administrator

	- Clear passwords must be at least six (6) characters in length.

	- Clear passwords must include characters from at least two (2) of these groupings: alpha, numeric, and special characters.

	- User should not be able to type a special characters that may have command function.

	- Clear passwords must not be the same as the userid with which they are associated, except the default local user passwords.

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                  | Range                                                                                                             |
+===========+==============================================================================================+===================================================================================================================+
| password  | Enter a clear text password for accessing DNOS IPMI.                                         | Clear passwords must include the following:                                                                       |
|           | If you do not enter a password, you will be prompted to enter a clear password for the user. | Minimum 6 characters, maximum 16.                                                                                 |
|           |                                                                                              | Must include a combination of at least 2 of the following groups: letters, numbers, special characters (e.g.@#$!) |
|           |                                                                                              | Special characters that have a command function (; & | ' ") are not allowed.                                      |
|           |                                                                                              | Must not contain a sequence of three or more characters from the previous password.                               |
|           |                                                                                              | The password must be different from the user-id (except for the default local user passwords)                     |
+-----------+----------------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ipmi
	dnRouter(cfg-system-login-ipmi)# user user1
	dnRouter(system-login-ipmi-user1)# password enc-!@#$%
	
	dnRouter(system-login-ipmi-user1)# password
	Enter password:
	Enter password for verification:
	
	


.. **Help line:** configure password for DNOS ipmi user.

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 10.0    | Command introduced                                   |
+---------+------------------------------------------------------+
| 13.0    | Replaced hashed password with encrypted password     |
+---------+------------------------------------------------------+
| 15.0    | Updated minimum length of password to six characters |
+---------+------------------------------------------------------+


