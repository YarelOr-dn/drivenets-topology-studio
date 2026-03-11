protocols pim address-family
----------------------------

**Minimum user role:** operator

To enter the PIM address-family interface configuration hierarchy:

**Command syntax: address-family [address-family]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+----------------+----------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                    | Range | Default |
+================+================================================================+=======+=========+
| address-family | PIM address-family and enters the PIM address-family hierarchy | ipv4  | \-      |
+----------------+----------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-rp)#


**Removing Configuration**

To remove the PIM address-family configuration:
::

    dnRouter(cfg-protocols-pim)# no address-family ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
