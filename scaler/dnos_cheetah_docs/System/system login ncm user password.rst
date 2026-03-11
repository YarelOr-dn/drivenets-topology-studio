system login ncm user password 
------------------------------

**Minimum user role:** operator

The password is a mandatory parameter for authentication. When creating new users, you must configure them with a password, otherwise the commit will fail. Once a password is configured, it cannot be deleted, only changed.

To set up a password or change an existing password for a user:

**Command syntax: password** {[encrypted-password] \| [password]}

**Command mode:** config

**Hierarchies**

- system login ncm user


**Note**

- Only users with an admin or techsupport role can edit passwords for users. Admins cannot edit the password for users with a techsupport role.

- Special characters that have a command function (; & | ' ") are not allowed.

- Clear passwords must include the following:

- Minimum 6 characters, maximum 16.

- Must include a combination of at least 2 of the following groups: letters, numbers, special characters (e.g.@#$!)

- Must not contain a sequence of three or more characters from the previous password.

- The password must be different from the user-id (except for the default local user passwords)

.. - One line command allows to enter password in encrypted format only.

	- It is not possible to remove password

	- If password with no value is entered, clear text password is requested with double confirmation

	**Validation:**

	- only DNOS user with admin/techsupport role can edit passwords for users

	- passwords length will be between 8-16 characters. operator which will insert other length will get an error message "passwords length should be between 8-16 characters"

	- clear passwords validations:

	   - clear passwords must include characters from at least two (2) of these groupings: alpha, numeric, and special characters. operator which will insert other length will get an error message "passwords must include characters from at least 2 of these groupings: alpha, numeric, and special characters"

	   - User should not be able to type a special characters that may have command function.

	   - clear passwords must not be the same as the user name with which they are associated.

**Parameter table**

+--------------------+--------------------------------+--------+---------+
| Parameter          | Description                    | Range  | Default |
+====================+================================+========+=========+
| encrypted-password | The new password for the user. | String | \-      |
+--------------------+--------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# ncm
	dnRouter(cfg-system-login-ncm)# user user1	
	dnRouter(system-login-ncm-user1)# password $6$qOB4/fW9kH0
	
	dnRouter(system-login-ncm-user1)# password
	Enter password:
	Enter password for verification:
	
	


.. **Help line:** configure password for NCM user.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+


