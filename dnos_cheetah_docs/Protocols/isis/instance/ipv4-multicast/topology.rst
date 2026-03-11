protocols isis instance address-family ipv4-multicast topology
--------------------------------------------------------------

**Minimum user role:** operator

Set if IS-IS will work with Multi-Topology and support a dedicated IPv4-Multicast topology MT ID #3.



**Command syntax: topology [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Note**

- reconfiguring topology admin-state will trigger LSP geneartion and new IS-IS IIH message with update topology information

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Set if ISIS will work with Multi-Topology and support a dedicated IPv4-Multicast | | enabled    | enabled |
|             | topology MT ID #3                                                                | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# topology enabled


**Removing Configuration**

To revert topology settings to default value:
::

    dnRouter(cfg-isis-inst-afi)# no topology

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
