protocols ospf instance area interface authentication-key md5 key-id password
-----------------------------------------------------------------------------

**Minimum user role:** operator

To set a password for authenticating the neighbor, peer group neighbors, or the neighbor in a peer group:

**Command syntax: authentication-key md5 key-id [key-id] password [secret]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- no command deletes key configuration.

- This configuration must be set if OSPF area authentication configuration is set.

- If no enc-password is set, the user must enter a clear password and verify it.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                      | Range            | Default |
+===========+==================================================================================+==================+=========+
| key-id    | md5 key id                                                                       | 1-255            | \-      |
+-----------+----------------------------------------------------------------------------------+------------------+---------+
| secret    | The encrypted password. If you do not set an encrypted password, you will be     | | string         | \-      |
|           | prompted to enter a clear password and verify it.                                | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1
    dnRouter(cfg-ospf-area-if)#  authentication-key md5 key-id 1 password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==
    dnRouter(cfg-ospf-area-if)#  authentication-key md5 key-id 2 password
    Enter password:
    Enter password for verification:


**Removing Configuration**

To delete the key configuration:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no authentication-key md5 key-id 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
