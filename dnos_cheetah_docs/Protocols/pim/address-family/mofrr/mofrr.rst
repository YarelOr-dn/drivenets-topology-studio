protocols pim address-family mofrr
----------------------------------

**Minimum user role:** operator

To enter the PIM MoFRR configuration hierarchy:

**Command syntax: mofrr**

**Command mode:** config

**Hierarchies**

- protocols pim address-family

**Example**
::

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)#


**Removing Configuration**

To return the PIM MoFRR configuration to its default values:
::

    dnRouter(cfg-protocols-pim-address-family)# no mofrr

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
