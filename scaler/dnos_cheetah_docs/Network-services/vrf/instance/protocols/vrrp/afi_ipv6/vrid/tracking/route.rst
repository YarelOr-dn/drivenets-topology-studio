network-services vrf instance protocols vrrp interface address-family ipv6 vrid tracking route vrf
--------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure tracking of route's reachability and reduce priority if it becomes unreachable:

**Command syntax: route [prefix] vrf [vrf-name]** priority-decrement [priority-decrement]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface address-family ipv6 vrid tracking
- protocols vrrp interface address-family ipv6 vrid tracking

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter          | Description                                                                      | Range      | Default |
+====================+==================================================================================+============+=========+
| prefix             | The IPv6 prefix of the network to track.                                         | X:X::X:X/x | \-      |
+--------------------+----------------------------------------------------------------------------------+------------+---------+
| vrf-name           | Routing instance to which the route belongs, or 'default'                        | \-         | \-      |
+--------------------+----------------------------------------------------------------------------------+------------+---------+
| priority-decrement | Specifies how much to decrement the priority of the VRRP router if there is a    | 1-254      | 10      |
|                    | failure in the IPv6 network.                                                     |            |         |
+--------------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# tracking
    dnRouter(cfg-afi-vrid-tracking)# route 2000:76CC::12/64 vrf default priority-decrement 100


**Removing Configuration**

To remove a specific route tracked for the VRRP group:
::

    dnRouter(cfg-afi-vrid-tracking)# no route 2000:76CC::12/64 vrf default

To revert the priority-decrement back to its default value for the specified tracked route:
::

    dnRouter(cfg-afi-vrid-tracking)# no route 2000:76CC::12/64 vrf default priority-decrement 30

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
