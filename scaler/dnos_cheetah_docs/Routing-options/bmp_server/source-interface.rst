routing-options bmp server source-interface
-------------------------------------------

**Minimum user role:** operator

To set the interface from which the source IP address for the BMP session will be taken.

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Note**

- The source IP type (IPv4 or IPv6) must match the server IP address-family. If one doesn't exist, the session will not open.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| source-interface | By default , uses the  "system in-band-management source-interface" for the same | | string         | \-      |
|                  | vrf                                                                              | | length 1-255   |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# source-interface lo0

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 2
    dnRouter(cfg-routing-option-bmp)# source-interface ge100-0/0/0


**Removing Configuration**

To return the source IP address to the default:
::

    dnRouter(cfg-routing-option-bmp)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
