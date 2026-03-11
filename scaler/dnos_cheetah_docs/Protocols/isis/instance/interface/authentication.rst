protocols isis instance interface authentication password
---------------------------------------------------------

**Minimum user role:** operator

To Enable hello messages authentication for the interface:

**Command syntax: authentication [type] password [enc-password]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Note**
- When typing a clear password, the password **won't** be displayed in the CLI terminal
- A clear password length cannot exceed 254 charachters
- Interface authentication is not applicable to loopback interfaces
..- The password is saved encrypted and always displayed as a secret

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-----------------------------------------------+---------+
| Parameter    | Description                                                                      | Range                                         | Default |
+==============+==================================================================================+===============================================+=========+
| type         | The type of authentication used.                                                 | | md5                                         | \-      |
|              |                                                                                  | | clear-text                                  |         |
+--------------+----------------------------------------------------------------------------------+-----------------------------------------------+---------+
| enc-password | The encrypted password. If you do not set an encrypted password, you will be     | A clear password cannot exceed 254 characters | \-      |
|              | prompted to enter a clear password and verify it.                                |                                               |         |
|              | When typing a clear password, the password will   not be displayed in the CLI    |                                               |         |
|              | terminal. The password format must match the encrypted format as displayed in    |                                               |         |
|              | "show config".                                                                   |                                               |         |
+--------------+----------------------------------------------------------------------------------+-----------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# authentication md5 password
    Enter password
    Enter password for verifications

    dnRouter(cfg-isis-inst-if)# authentication md5 password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-isis-inst-if)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
