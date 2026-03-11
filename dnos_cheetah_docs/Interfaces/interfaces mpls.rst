interfaces mpls
---------------

**Minimum user role:** operator

MPLS is a packet-forwarding technology which uses labels in order to make data forwarding decisions. With MPLS, the Layer 3 header analysis is done just once (when the packet enters the MPLS domain). Label inspection drives subsequent packet forwarding. Additionally, it decreases the forwarding overhead on the core routers. When disabled, all mpls traffic received on the interface will be dropped.

To enable MPLS on an interface, use the following command in configuration mode:

**Command syntax: mpls [mpls-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+------------+------------------------------------------------------+--------------+----------+
| Parameter  | Description                                          | Range        | Default  |
+============+======================================================+==============+==========+
| mpls-state | Enables or disables MPLS on the specified interface. | | enabled    | disabled |
|            |                                                      | | disabled   |          |
+------------+------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-1/1/1
    dnRouter(cfg-if-ge10-1/1/1)# mpls enabled

    dnRouter(cfg-if)# ge10-1/1/1.100
    dnRouter(cfg-if-ge10-1/1/1.100)# mpls enabled

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# mpls disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no mpls

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
