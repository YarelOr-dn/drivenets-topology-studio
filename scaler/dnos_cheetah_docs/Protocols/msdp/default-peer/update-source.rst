protocols msdp default-peer update-source
-----------------------------------------

**Minimum user role:** operator

You can use the following command to set the default-peer source IP address. The source IP can be set either by specifying the source IP or the interface on which the desired IP is set.

**Command syntax: update-source {source-address [source-ip], interface [interface-name]}**

**Command mode:** config

**Hierarchies**

- protocols msdp default-peer

**Note**
- There is no default setting for update-source. Once the update-source is defined, the default-peer or mesh-group are set.

- These is no remove option for update-source. You can only change the assigned address of the update-source, unless the whole default-peer or mesh-groups are removed.

**Parameter table**

+----------------+----------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                          | Range            | Default |
+================+======================================================================+==================+=========+
| source-ip      | specify the source address to use for the MSDP  session to this peer | A.B.C.D          | \-      |
+----------------+----------------------------------------------------------------------+------------------+---------+
| interface-name | Interface from which the source address is taken                     | | string         | \-      |
|                |                                                                      | | length 1-255   |         |
+----------------+----------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# update-source source-address 3.3.3.3

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# update-source interface lo0


**Removing Configuration**

To return the update-source to the default:
::

    dnRouter(cfg-protocols-msdp-default-peer)# no update-source

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
