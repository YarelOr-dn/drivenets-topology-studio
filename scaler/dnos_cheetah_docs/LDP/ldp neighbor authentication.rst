ldp neighbor authentication
---------------------------

**Minimum user role:** operator

Sets the LDP neighbor authentication mode (None or MD5). When MD5 mode is set, the authentication password must be set. This per-neighbor configuration overrides the global LDP authentication configuration. When set to "none", the LDP neighbor will not be authenticated.

**Command syntax: authentication {none | md5 password** [enc-password] **}**

**Command mode:** config

**Hierarchies**

- protocols ldp neighbor 

.. 
	**Note:**

	- LDP neighbor TCP session is set using the global default LDP authentication configuration. Alternatively the user may override the authentication configuration per neighbor.

	- Configuration applies also for targeted LDP session

	- 'authentication none' disables authentication for the specified LDP neighbor.

	- 'authentication md5 password' enables MD5 authentication and sets the password.

	- When typing a clear text password, the password and retyping won't be displayed in the CLI terminal
	
	- Clear text password length is 1-80 characters
	
	- Enc-password must be a valid dnRouter encrypted password
	
	- Changing authentication configuration restarts the relevant LDP neighbor TCP session.
	
	- Password is saved encrypted and always displayed as secret
	
	- 'no authentication' reverts the authentication settings to the global default LDP authentication settings.

**Parameter table**

+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                 |                                                                                                                                                                                                                                                                                                                                            |                     |             |
| Parameter       | Description                                                                                                                                                                                                                                                                                                                                | Range               | Default     |
+=================+============================================================================================================================================================================================================================================================================================================================================+=====================+=============+
|                 |                                                                                                                                                                                                                                                                                                                                            |                     |             |
| enc-password    | The password to be used for the session TCP connection with the specified neighbor. The password must be a valid encrypted password (the password was encrypted by a dnRouter).                                                                                                                                                            | string              | \-          |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+
|                 |                                                                                                                                                                                                                                                                                                                                            |                     |             |
| clear-text      | If you do not specify a password, enter the password of the LDP neighbor router in clear text. The password is then encrypted and from then on will be displayed as encrypted. You can copy the encrypted password and   use it as the enc-password. When typing a clear password, the password is not   displayed in the CLI terminal.    | 1..80 characters    | \-          |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)# authentication md5 password
	Enter password:
	Enter password for verification:

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)# authentication md5 password enc-!344fGVkX1+

**Removing Configuration**

To disable authentication for a specified LDP neighbor:
::

 	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)# authentication none

To revert the authentication settings to the global default LDP authentication settings:
::

	dnRouter(cfg-protocols-ldp-neighbor)# no authentication

.. **Help line:** Sets LDP neighbor authentication configuration.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+
