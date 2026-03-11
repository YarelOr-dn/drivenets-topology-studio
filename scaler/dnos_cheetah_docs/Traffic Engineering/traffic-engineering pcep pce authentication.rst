traffic-engineering pcep pce authentication
-------------------------------------------

**Minimum user role:** operator

To protect the PCEP TCP sessions between the PCE and PCC using MD5 authentication algorithm:

**Command syntax: authentication [admin-state] password** [enc-password]

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce

**Note**

- When authentication is enabled, unauthenticated packets will be dropped.

..
	**Internal Note**

	-  when typing a clear password, the password **won't** be displayed in the CLI terminal

	-  password is saved encrypted, and always displayed as secret

	-  unauthenticated packets will be dropped

**Parameter table**

+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------------------------+
|                 |                                                                                                                                       |             |                               |
| Parameter       | Description                                                                                                                           | Range       | Default                       |
+=================+=======================================================================================================================================+=============+===============================+
|                 |                                                                                                                                       |             |                               |
| admin-state     | Enable/disable PCEP session protection with the   PCE                                                                                 | Enabled     | The TE PCEP authentication    |
|                 |                                                                                                                                       |             |                               |
|                 |                                                                                                                                       | Disabled    |                               |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------------------------+
|                 |                                                                                                                                       |             |                               |
| enc-password    | The encrypted password. If you do not set an   encrypted password, you will be prompted to enter a clear password and verify   it.    | String      | \-                            |
+-----------------+---------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# authentication enabled password
	Enter password:
	Enter password for verifications:
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==
	
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKPVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVZ-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# authentication disabled

**Removing Configuration**

To revert PCE authentication to the default state (defined by PCEP):
::

	dnRouter(cfg-te-pcep-pce)# no authentication


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+