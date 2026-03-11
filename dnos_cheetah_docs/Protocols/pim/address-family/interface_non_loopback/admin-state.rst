protocols pim address-family interface admin-state
--------------------------------------------------

**Minimum user role:** operator

To enable/disable PIM on an interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family interface

**Note**
- Using 'admin-state disabled' command disables pim on the interface; using the 'no' command also removes the interface from the PIM protocol scope.

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | Enables/disables PIM on an interface | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface bundle-20.101
    dnRouter(cfg-protocols-pim-af4-if)# admin-state enabled
    dnRouter(cfg-protocols-pim-af4-if)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface ge100-1/2/1 admin-state enabled
    dnRouter(cfg-protocols-pim-af4)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-af4)# interface bundle-23.1
    dnRouter(cfg-protocols-pim-af4-if)# admin-state disabled
    dnRouter(cfg-protocols-pim-af4-if)#


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-pim-af4)# no interface bundle-3.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
