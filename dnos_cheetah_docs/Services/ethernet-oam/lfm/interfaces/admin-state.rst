services ethernet-oam link-fault-management interface admin-state
-----------------------------------------------------------------

**Minimum user role:** operator

To configure the administrative state of the 802.3ah EFM OAM protocol on the specified interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management interface

**Parameter table**

+-------------+-------------------------------------------------------+--------------+----------+
| Parameter   | Description                                           | Range        | Default  |
+=============+=======================================================+==============+==========+
| admin-state | 802.3ah EFM OAM administrative state on the interface | | enabled    | disabled |
|             |                                                       | | disabled   |          |
+-------------+-------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# interface ge100-0/0/0
    dnRouter(cfg-eoam-lfm-if)# admin-state enabled


**Removing Configuration**

To return 802.3ah EFM OAM admin-state on the interface to its default value:
::

    dnRouter(cfg-eoam-lfm-if)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
