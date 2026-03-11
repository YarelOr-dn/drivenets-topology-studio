protocols ospf instance area interface authentication-key password
------------------------------------------------------------------

**Minimum user role:** operator

If the OSPF area authentication is configured, you must set the OSPF authentication key to a cryptographic password for the interface.
To configure the interface authentication key:

**Command syntax: authentication-key password [secret]**

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
| secret    | The encrypted password. If you do not set an encrypted password, you will be     | | string         | \-      |
|           | prompted to enter a clear password and verify it.                                | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)#  authentication-key password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==


**Removing Configuration**

To delete the key configuration: 
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)#  no authentication-key password

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
