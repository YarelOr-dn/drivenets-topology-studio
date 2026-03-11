protocols ospfv3 area authentication spi
----------------------------------------

**Minimum user role:** operator

Use authentication to guarantee that only trusted devices participate in the area’s routing.
To configure the default authentication method for the OSPFv3 interfaces in the area:

**Command syntax: authentication [authentication-type] spi [spi] [ipsec-authentication-algorithm] password [secret]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area

**Note**

- Authentication is disabled by default.

- IPsec - IPsec is the expected authentication for all OSPFv3 packets over the interface.

- If the authentication secret is not entered with the command, then the user will be prompted to enter a clear-text password and verify it. This password will be saved in encrypted format.

**Parameter table**

+--------------------------------+----------------------------------------------------------------------------------+------------------+-----------------------------------------------+
| Parameter                      | Description                                                                      | Range            | Default                                       |
+================================+==================================================================================+==================+===============================================+
| authentication-type            | The authentication type that is used on the interface.                           | ipsec            | no authentication unless default set for area |
+--------------------------------+----------------------------------------------------------------------------------+------------------+-----------------------------------------------+
| spi                            | The Security Parameter Index (SPI) value.                                        | 256-4294967295   | \-                                            |
+--------------------------------+----------------------------------------------------------------------------------+------------------+-----------------------------------------------+
| ipsec-authentication-algorithm | The IPsec AH authentication algorithm.                                           | md5              | \-                                            |
+--------------------------------+----------------------------------------------------------------------------------+------------------+-----------------------------------------------+
| secret                         | The encrypted password. If you do not set an encrypted password, you will be     | | string         | \-                                            |
|                                | prompted to enter a clear password and verify it.                                | | length 1-255   |                                               |
+--------------------------------+----------------------------------------------------------------------------------+------------------+-----------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# authentication ipsec spi 256 md5 password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# authentication ipsec spi 256 md5 password
    Enter password:
    Enter password for verification:


**Removing Configuration**

To disable the authentication requirement for OSPFv3 packets on the area:
::

    dnRouter(cfg-ospfv3-area-if)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
