interfaces l2-service
---------------------

**Minimum user role:** operator

To configure a sub-interface as an L2 service UNI port:

**Command syntax: l2-service [l2-service-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

- A sub-interface can be configured as an L2 service UNI port only if there are no IPv4 or IPv6 addresses and no other conflicting settings (such as access-lists) configured on it.

**Parameter table**

+------------------+-----------------------------------------------+--------------+----------+
| Parameter        | Description                                   | Range        | Default  |
+==================+===============================================+==============+==========+
| l2-service-state | The state of the L2 service on this interface | | enabled    | disabled |
|                  |                                               | | disabled   |          |
+------------------+-----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-100.2
    dnRouter(cfg-if-bundle-100.2)# l2-service enabled

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1.22 l2-service disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-bundle-100.2)# no l2-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
