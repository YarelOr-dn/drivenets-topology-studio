system aaa-server tacacs server priority address password
---------------------------------------------------------

**Minimum user role:** operator

Configure a password for the TACACS+ server.

The password must match the password configured on the AAA server. You can enter the password in plain-text, but it will be displayed in an encrypted form with an enc-prefix in any show command. The encryption is performed with the same key used by the system to decrypt the password during load/copy of configuration.

If you do not enter a password, you will be prompted for the (unencrypted) password.

To define a password for the remote TACACS+ server:


**Command syntax: password [password]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- You will not be able to commit the configuration without a configured password.

-  The password configuration is optional for a TACACS+ erver (clear or encrypted). This means that you can configure a TACACS+ server without a shared key at both the client device and the security server if you do not want the connection to be encrypted. This might be useful for a lab or training environment but is strongly discouraged in a production environment.

..

  -  The password can be made up of ASCII alphanumeric characters ([A-Za-z0-9]).

  -  The password must be between 1 to 64 characters.

  -  At least 1 alphabet character must be configured.

  -  If a password is not configured, the commit fails.


**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------------------------+---------+
| Parameter | Description                                                                      | Range                   | Default |
+===========+==================================================================================+=========================+=========+
| password  | The shared secret between the device and the AAA server that is used to          | string 1..64 characters | \-      |
|           | authenticate requests and replies.                                               |                         |         |
|           | The length of the password must be between 1 and 64 ASCII alphanumeric           |                         |         |
|           | characters (A-Z, a-z, 0-9), with at least one letter.                            |                         |         |
+-----------+----------------------------------------------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# password enc-!@#$%
    dnRouter(cfg-aaa-tacacs-server)# password
    Enter password
    Enter password for verifications


**Removing Configuration**

Once configured, the password cannot be deleted, only changed.
::

    \-


**Command History**

+---------+---------------------------------------------------------------------------+
| Release | Modification                                                              |
+=========+===========================================================================+
| 5.1.0   | Command introduced                                                        |
+---------+---------------------------------------------------------------------------+
| 6.0     | Replaced "secret" with "password" in syntax                               |
|         | Applied new hierarchy                                                     |
+---------+---------------------------------------------------------------------------+
| 10.0    | Applied new hierarchy                                                     |
+---------+---------------------------------------------------------------------------+
| 11.0    | Changed the minimum length of the password, moved to "server" hierarchy   |
+---------+---------------------------------------------------------------------------+
| 15.2    | Password is now optional                                                  |
+---------+---------------------------------------------------------------------------+
