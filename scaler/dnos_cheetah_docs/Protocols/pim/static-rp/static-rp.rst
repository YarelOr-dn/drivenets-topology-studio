protocols pim static-rp
-----------------------

**Minimum user role:** operator

Use the following command to configure the static RP IP address. The IP address is typically a loopback IP address. It can be a local IP address, in which case the local router is defined as the RP, or a different router-id IP address. If the RP address is configured without a defined range, it will be mapped to all of the IP multicast 224.0.0.0/4 group ranges.

**Command syntax: static-rp [static-rp]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Parameter table**

+-----------+---------------+---------+---------+
| Parameter | Description   | Range   | Default |
+===========+===============+=========+=========+
| static-rp | PIM static RP | A.B.C.D | \-      |
+-----------+---------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# static-rp 2.2.2.2
    dnRouter(cfg-protocols-pim-rp)#


**Removing Configuration**

To remove the RP address group mapping:
::

    dnRouter(cfg-protocols-pim)# no static-rp 2.2.2.2

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
