ldp authentication
------------------

**Minimum user role:** operator

To set the MD5 authentication password for all LDP neighbors. Changing the authentication configuration will cause all LDP sessions to restart unless they have a per-neighbor authentication configuration, which will override this setting.

**Command syntax: authentication md5 password** [enc-password]

**Command mode:** config

**Hierarchies**

- protocols ldp 

**Note**

- If a password is not provided with the command, you will be prompted to enter a clear-text password. The clear-text password is 1-80 charachters long.

..
	Configuration applies also for targeted LDP session, unless more specific setting exist

	When authentication password is specified authentication is set on TCP sessions by default.

	When typing a clear text password, the password and retyping won't be displayed in the CLI terminal

	Clear text password length is 1-80 charachters

	enc-password must be a valid dnRouter encrypted password

	changing authentication configuration will cause all LDP sessions to restart unless they have an overriding per neighbor configuration for authentication

	password is saved encrypted, and always displayed as secret

	'no authentication' disables authentication as default configuration. This results in restarting LDP neighbor sessions, for which there is no override authentication configuration.

**Parameter table**

+-----------------+----------------------------------------------+-----------+-------------+
|                 |                                              |           |             |
| Parameter       | Description                                  | Range     | Default     |
+=================+==============================================+===========+=============+
|                 |                                              |           |             |
| enc-password    | The encrypted password for LDP neighbors.    | string    | \-          |
+-----------------+----------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# authentication md5 password
	Enter password:
	Enter password for verification:

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# authentication md5 password enc-!344fGVkX1+

**Removing Configuration**

To disable the authentication:
::

	dnRouter(cfg-protocols-ldp)# no authentication

.. **Help line:** Sets default MD5 authentication password for all LDP neighbors.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+
