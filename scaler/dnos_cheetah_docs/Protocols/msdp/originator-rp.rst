protocols msdp originator-rp
----------------------------

**Minimum user role:** operator

You can use this command to enable setting the IP address or specify the interface to be the RP address of the MSDP SA messages originated by the local MSDP router.

**Command syntax: originator-rp {source-address [source-address], interface [interface-name]}**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
- The originator-rp must have default or be configured. If it is not configured, the default originator-rp will be the router-id.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                                      | Range            | Default |
+================+==================================================================================+==================+=========+
| source-address | specify the originator ID source address to use for the MSDP session to this     | A.B.C.D          | \-      |
|                | peer                                                                             |                  |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+
| interface-name | Specify the interface name from which the MSDP originator RP IP address shall be | | string         | \-      |
|                | taken                                                                            | | length 1-255   |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# originator-rp interface lo0
    dnRouter(cfg-protocols-msdp)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# originator-rp source-address 1.1.1.1
    dnRouter(cfg-protocols-msdp)#


**Removing Configuration**

To return the originator-rp setting to its default value:
::

    dnRouter(cfg-protocols-msdp)# no originator-rp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
