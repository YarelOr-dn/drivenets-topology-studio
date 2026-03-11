network-services vrf instance protocols vrrp interface address-family ipv6 vrid priority
----------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the priority level for the VRRP group:

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface address-family ipv6 vrid
- protocols vrrp interface address-family ipv6 vrid

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| priority  | Specifies the sending VRRP interface's priority for the virtual router.  Higher  | 1-254 | 100     |
|           | values equal higher priority                                                     |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# priority 240


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
