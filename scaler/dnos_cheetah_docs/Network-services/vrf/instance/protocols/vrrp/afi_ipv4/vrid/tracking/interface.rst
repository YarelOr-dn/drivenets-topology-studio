network-services vrf instance protocols vrrp interface address-family ipv4 vrid tracking interface
--------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure tracking of interface's operational status and reduce priority if it goes down:

**Command syntax: interface [tracked-interface]** priority-decrement [priority-decrement]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface address-family ipv4 vrid tracking
- protocols vrrp interface address-family ipv4 vrid tracking

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+----------------------------------------+---------+
| Parameter          | Description                                                                      | Range                                  | Default |
+====================+==================================================================================+========================================+=========+
| tracked-interface  | Track an interface                                                               | | geX-<f>/<n>/<p>                      | \-      |
|                    |                                                                                  | | geX-<f>/<n>/<p>.<sub-interface-id>   |         |
|                    |                                                                                  | | bundle-<bundle-id>                   |         |
|                    |                                                                                  | | bundle-<bundle-id.sub-bundle-id>     |         |
|                    |                                                                                  | | loX                                  |         |
|                    |                                                                                  | | irb<0-65535>                         |         |
+--------------------+----------------------------------------------------------------------------------+----------------------------------------+---------+
| priority-decrement | Specifies how much to decrement the priority of the VRRP instance if the         | 1-254                                  | 10      |
|                    | interface goes down                                                              |                                        |         |
+--------------------+----------------------------------------------------------------------------------+----------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# tracking
    dnRouter(cfg-afi-vrid-tracking)# interface bundle-2 priority-decrement 25


**Removing Configuration**

To remove a specific interface tracked for the VRRP group:
::

    dnRouter(cfg-afi-vrid-tracking)# no interface bundle-2

To revert the priority-decrement back to its default value for the specified tracked interface:
::

    dnRouter(cfg-afi-vrid-tracking)# no interface bundle-2 priority-decrement 30

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
