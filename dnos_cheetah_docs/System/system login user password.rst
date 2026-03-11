system login user password
--------------------------

**Minimum user role:** admin

The password is a mandatory parameter for authentication. When creating new users, you must configure them with a password, otherwise the commit will fail. Once a password is configured, it cannot be deleted, only changed.

To set up a password or change an existing password for a user:

**Command syntax: user [user-name]** password {[hashed-password] \| [password]}

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- Only users with an admin or techsupport role can edit passwords for users. Admins cannot edit the password for users with a techsupport role.

- Special characters that have a command function (' ') are not allowed.

- You are required to have a password or an SSH public key.

If you enter the password command without a hashed-password, you will be prompted to enter a clear text password with double confirmation.
Clear passwords must include the following:

- Clear passwords must be at least eight (8) characters in length.

- Must include a combination of at least 2 of the following groups: letters, numbers, special characters (e.g.@#$!)

- The password must be different from the user-id (except for the default local user passwords)

.. - One line command allows to enter password in SHA-512 format only.

	- no command removes the password.

	- If password with no value is entered, clear text password is requested with double confirmation

	**Validation:**

	- User must have either a password or an SSH public key or both.

	- only user with admin/techsupport role can edit passwords for users

	- user with role admin, cannot edited password for user in techsupport role

	- Clear passwords must be at least eight (8) characters in length.

	- Clear passwords must include characters from at least two (2) of these groupings: alpha, numeric, and special characters.

	- User should not be able to type a special characters that may have command function.

	- Clear passwords must not be the same as the userid with which they are associated, except the default local user passwords.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------+
| Parameter       | Description                                                                                |
+=================+============================================================================================+
| hashed-password | Enter the user's existing password. The password is inserted as a hashed string (SHA-512). |
+-----------------+--------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName2
	dnRouter(cfg-system-login-MyUserName2)# password $6$qOB4/fW9kH0yWvta$MF4iWvbAztfrbOBKAQLZ7GCFO7wVhUY4GoILSs/4HtG1QP8TjzPiQQ33B0J/t3ReeEHARLNR3QnMzFowTgETR.

	dnRouter(cfg-system-login-MyUserName2)# password
	Enter password:
	Enter password for verification:



**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName2)# no password

.. **Help line:** Configure user password

**Command History**

+---------+--------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                     |
+=========+==================================================================================================+
| 5.1.0   | Command introduced                                                                               |
+---------+--------------------------------------------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                                                            |
+---------+--------------------------------------------------------------------------------------------------+
| 10.0    | Applied new hierarchy                                                                            |
+---------+--------------------------------------------------------------------------------------------------+
| 11.2    | Added note about forbidden special characters.                                                   |
+---------+--------------------------------------------------------------------------------------------------+
| 15.0    | Added the option to remove the password and updated minimum length of password to six characters |
+---------+--------------------------------------------------------------------------------------------------+
| 19.1    | Updated minimum length of password to eight characters                                           |
+---------+--------------------------------------------------------------------------------------------------+
