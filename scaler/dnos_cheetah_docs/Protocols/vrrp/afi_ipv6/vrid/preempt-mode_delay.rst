protocols vrrp interface address-family ipv6 vrid preempt-mode delay
--------------------------------------------------------------------

**Minimum user role:** operator

To set the preeempt delay to wait before a backup router will attempt preempting the master for the VRRP group:

**Command syntax: preempt-mode delay [preempt-delay]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv6 vrid
- network-services vrf instance protocols vrrp interface address-family ipv6 vrid

**Parameter table**

+---------------+------------------------------------------------------------------+--------+---------+
| Parameter     | Description                                                      | Range  | Default |
+===============+==================================================================+========+=========+
| preempt-delay | Set the delay the higher priority router waits before preempting | 0-3600 | 1       |
+---------------+------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# preempt-mode delay 1


**Removing Configuration**

To return the preempt-mode delay to its default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no preempt-mode delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
