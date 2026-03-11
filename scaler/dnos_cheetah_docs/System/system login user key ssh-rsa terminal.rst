system login user key ssh-rsa terminal
--------------------------------------

**Minimum user role:** operator

Public key authentication is step forward to the security improvement of password-protected systems. It provides a cryptographic strength that is considerably stronger than conventional passwords (even if they are extremely long or complicated). With SSH, authentication using a public key dismisses the need of users creating and remembering complex passwords.

Once you have generated a private-public key (outside of DNOS), the public key needs to be verified by DNOS to be a valid SSH RSA public key. You can then login to the CLI and NETCONF using the matching private key.

To configure a user public key from a terminal:

**Command syntax: user [user-name]** key ssh-rsa terminal [public-key-string]

**Command mode:** config

**Hierarchies**

- system login user


**Note**

- If a username doesn't exist, a new user will be created.

- You are required to have a password or an SSH public key, but if both exist you can use either to authenticate.

.. - no command removes the key.

	- If user name does not exist, new user is created.

	- User that has both password and SSH key may authenticate with either.

	**Validation:**

	- User must have either a password or an SSH public key or both.

**Parameter table**

+-------------------+-------------------------------------------------+--------+---------+
| Parameter         | Description                                     | Range  | Default |
+===================+=================================================+========+=========+
| public-key-string | The SSHv2 RSA public key in OpenSSH format:     | String | \-      |
|                   | ssh-rsa <base64-encoded key> [optional comment] |        |         |
+-------------------+-------------------------------------------------+--------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# login
	dnRouter(cfg-system-login)# user MyUserName
	dnRouter(cfg-system-login-MyUserName)# key ssh-rsa terminal "ssh-rsa AAAAB3NzaC1yc2EAAA...D4I7SFrQ== MyUserName@My-MacBook-Pro"
	dnRouter(cfg-system-login)# user AnotherUser
	dnRouter(cfg-system-login-AnotherUser)# key ssh-rsa terminal "ssh-rsa AAAAFGbnj1yc2EAAA...D4I8KJd6=="


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
