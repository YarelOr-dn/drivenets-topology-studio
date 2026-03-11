network-services vrf instance protocols bgp neighbor address-family long-lived-graceful-restart admin-state
-----------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable/disable long-lived-graceful-restart feature on a neighbor/neighbor-group

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor address-family long-lived-graceful-restart

**Note**

- The command is applicable to BGP neighbor and neighbor-groups

- The Graceful restart capability must be enabled for the LLGR to be enabled

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | The administrative state of the long lived graceful restart feature for the      | | enabled    | disabled |
|             | specific neighbor/neighbor-group. When enabled, peer will be configured with     | | disabled   |          |
|             | long lived graceful restart parameters.                                          |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# long-lived-graceful-restart
    dnRouter(cfg-neighbor-afi-llgr)# admin-state enabled


**Removing Configuration**

To revert all BGP long-lived-graceful-restart parameters to their default values: 
::

    dnRouter(cfg-neighbor-afi-llgr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
