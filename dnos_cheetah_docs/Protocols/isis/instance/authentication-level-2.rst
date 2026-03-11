protocols isis instance authentication level level-2 type password
------------------------------------------------------------------

**Minimum user role:** operator

LSP packets are not authenticated by default. You can configure authentication for LSP and NSP packets, so that unauthenticated packets will be dropped.

To configure authentication:


**Command syntax: authentication level level-2 type [type] password [enc-password]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**
- When typing a clear password, the password **won't** be displayed in the CLI terminal.
- A clear password length cannot exceed 254 charachters.
- Interface authentication is not applicable to loopback interfaces.
..- The password is saved encrypted and always displayed as a secret


**Parameter table**

+--------------+----------------------------------------------------------------------------------+-------------------------------+---------+
| Parameter    | Description                                                                      | Range                         | Default |
+==============+==================================================================================+===============================+=========+
| type         | The type of authentication used.                                                 | | md5                         | \-      |
|              |                                                                                  | | clear-text                  |         |
+--------------+----------------------------------------------------------------------------------+-------------------------------+---------+
| enc-password | Enter the encrypted password string for the area. The password must be a valid   | clear-text: 1..254 characters | \-      |
|              | encrypted password (the password was encrypted by a dnRouter).                   |                               |         |
|              | When typing a clear password, the password will not be displayed in the CLI      |                               |         |
|              | terminal. The password format must match the encrypted format as displayed in    |                               |         |
|              | "show config".                                                                   |                               |         |
+--------------+----------------------------------------------------------------------------------+-------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# authentication level level-2 type md5 password
    Enter password
    Enter password for verifications
    dnRouter(cfg-protocols-isis-inst)# authentication level level-2 type md5 password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==


**Removing Configuration**

To stop authentication for a specific level:
::

    dnRouter(cfg-protocols-isis-inst)# no authentication level level-2

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 9.0     | Command introduced                         |
+---------+--------------------------------------------+
| 10.0    | Removed "no authentication" for all levels |
+---------+--------------------------------------------+
