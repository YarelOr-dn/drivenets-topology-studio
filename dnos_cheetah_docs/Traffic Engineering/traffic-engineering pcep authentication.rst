traffic-engineering pcep authentication
---------------------------------------

**Minimum user role:** operator

To protect all PCEP TCP sessions between PCE and PCC using MD5 authentication algorithm:

**Command syntax: authentication [admin-state] password** [enc-password]

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Note**

- When authentication is enabled, unauthenticated packets will be dropped.

- When typing a clear password, the password is not displayed in the CLI terminal. The password is saved encrypted and is always displayed as secret.

**Parameter table**

+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                 |                                                                                                                                       |             |             |
| Parameter       | Description                                                                                                                           | Range       | Default     |
+=================+=======================================================================================================================================+=============+=============+
|                 |                                                                                                                                       |             |             |
| admin-state     | Enable/disable PCEP session protection                                                                                                | Enabled     | Disabled    |
|                 |                                                                                                                                       |             |             |
|                 |                                                                                                                                       | Disabled    |             |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                 |                                                                                                                                       |             |             |
| enc-password    | The encrypted password. If you do not set an   encrypted password, you will be prompted to enter a clear password and verify   it.    | String      | \-          |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# authentication enabled password
	Enter password:
	Enter password for verifications:
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==

**Removing Configuration**

To revert PCE authentication to the default state:
::

	dnRouter(cfg-mpls-te-pcep)# no authentication


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+