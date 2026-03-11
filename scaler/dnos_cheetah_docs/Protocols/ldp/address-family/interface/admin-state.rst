protocols ldp address-family interface admin-state
--------------------------------------------------

**Minimum user role:** operator

Setting the LDP interface to disable mode. The interface will not send or receive LDP packets.

To set the LDP interface to disable mode:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family interface

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | Administratively set the LDP state | | enabled    | enabled |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ldp
    dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-ldp-afi)# interface ge100-0/0/0
    dnRouter(cfg-ldp-afi-if)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-ldp-afi-if)# no admin-state disabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
