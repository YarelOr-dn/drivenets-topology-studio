protocols isis instance authentication level level-1 snp-auth
-------------------------------------------------------------

**Minimum user role:** operator

SNP packets are not authenticated by default. You can enable SNP packet authentication, so that unauthenticated packets will be dropped.

To configure authentication:


**Command syntax: authentication level level-1 snp-auth [snp-auth]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**
- SNP packet authentication is only possible if IS-IS authentication for LSP packets is enabled for the same level.


**Parameter table**

+-----------+--------------------------------------------+---------------------------------------------------------------------------------+----------+
| Parameter | Description                                | Range                                                                           | Default  |
+===========+============================================+=================================================================================+==========+
| snp-auth  | Set the authentication mode of SNP packets | | disabled - no SNP authentication                                              | disabled |
|           |                                            | | sign - only sign outgoing SNP packets                                         |          |
|           |                                            | | sign-validate - sign outgoing SNP packets and validate incoming SNP packets   |          |
+-----------+--------------------------------------------+---------------------------------------------------------------------------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# authentication level-2 snp-auth sign

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# authentication level level-1 snp-auth sign-validate

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# authentication level level-2 snp-auth sign-validate


**Removing Configuration**

To revert SNP-auth to the default value:
::

    dnRouter(cfg-protocols-isis-inst)# no authentication level level-2 snp-auth
    dnRouter(cfg-protocols-isis-inst)# no authentication level level-1 snp-auth

**Command History**

+---------+-----------------------------+
| Release | Modification                |
+=========+=============================+
| 9.0     | Command introduced          |
+---------+-----------------------------+
| 14.0    | Added support for level-1-2 |
+---------+-----------------------------+
| 15.0    | Updated command syntax      |
+---------+-----------------------------+
