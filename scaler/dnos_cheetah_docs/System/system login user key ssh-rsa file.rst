system login user key ssh-rsa file
--------------------------------------

**Minimum user role:** admin

Public key authentication is step forward to the security improvement of password-protected systems. It provides a cryptographic strength that is considerably stronger than conventional passwords (even if they are extremely long or complicated). With SSH, authentication using a public key dismisses the need of users creating and remembering complex passwords.

You can use this command to import an SSH public key from a file located in the ssh-keys directory. You can then login to the CLI and NETCONF using the matching private key.

To import a public key from a file for a user:

**Command syntax: user [user-name]** key ssh-rsa file [filename]

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- The public key file must be located in the NCC ssh-keys directory and must contain one line in the format "ssh-rsa <base64-encoded key> [optional comment]". Empty lines and lines beginning with '#' will be ignored.

- You are required to have a password or an SSH public key, but if both exist you can use either to authenticate.

.. - no command removes the key.

	- User that has both password and SSH key may authenticate with either.

	**Validation:**

	- User must have either a password or an SSH public key or both.

	- The file must be found in NCC ssh-keys directory.

	- The file must contain one line in the format "ssh-rsa <base64-encoded key> [optional comment]". Empty lines and lines starting with '#' are ignored.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| filename  | The name of the file where the public key is located. | String | \-      |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# key ssh-rsa file john_id_rsa.pub


**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-login-MyUserName)# no key

.. **Help line:** Configure SSH user public key for key-based login to CLI and NETCONF.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
