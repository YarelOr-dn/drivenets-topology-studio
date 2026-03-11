protocols pim address-family interface
--------------------------------------

**Minimum user role:** operator

To enter the PIM address-family interface configuration hierarchy:

**Command syntax: interface [non-loopback-interface]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family

**Parameter table**

+------------------------+------------------+------------------+---------+
| Parameter              | Description      | Range            | Default |
+========================+==================+==================+=========+
| non-loopback-interface | PIM on interface | | string         | \-      |
|                        |                  | | length 1-255   |         |
+------------------------+------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface ge100-1/2/1
    dnRouter(cfg-protocols-pim-af4-if)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface bundle-20.101
    dnRouter(cfg-protocols-pim-af4-if)#


**Removing Configuration**

To disable PIM on the interface and clear the PIM related configuration:
::

    dnRouter(cfg-protocols-pim-af4)# no interface bundle-3.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
