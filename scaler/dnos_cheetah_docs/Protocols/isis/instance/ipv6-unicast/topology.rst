protocols isis instance address-family ipv6-unicast topology
------------------------------------------------------------

**Minimum user role:** operator

Traditionally, when running IPv4 and IPv6 simultaneously, IS-IS can operate in single-topology or multi-topology mode. In single topology, a single topology is generated for both IPv4 and IPv6 and SPF calculations are done on both address-families simulatenously. In multi-topology, IPv4 and IPv6 prefixes are separated on different topologies and the SPF calculations are therefore also done separately.

To configure whether IS-IS will work with multi-topology and support a dedicated IPv6-Unicast topology (MT ID #2 - RFC5120):

**Command syntax: topology [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**

- Reconfiguring the topology admin-state will trigger LSP generation and a new IS-IS IIH message will be created with the updated topology information.

- Disabling ipv6-unicast topology does not automatically switch to single topology as other topologies (e.g. multicast) may be enabled.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Set if ISIS will work with Multi-Topology and support a dedicated IPv6-Unicast   | | enabled    | enabled |
|             | topology MT ID #2                                                                | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# topology disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-isis-inst-afi)# no topology

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2    | Command introduced |
+---------+--------------------+
