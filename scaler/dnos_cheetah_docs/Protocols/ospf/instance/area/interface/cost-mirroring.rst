protocols ospf instance area interface cost-mirroring
-----------------------------------------------------

**Minimum user role:** operator

OSPF cost mirroring automatically sets an interface OSPF cost according to the adjacent neighbor OSPF LSA update for the local interface. When an adjacent OSPF neighbor is applied with an OSPF lag-cost-fallback which dynamically sets the OSPF cost of a bundle interface according to the number of members in the bundle, a local OSPF neighbor can adjust the OSPF cost on the local bundle interface to accommodate the change without the need to support OSPF lag-cost-fallback locally. Cost mirroring can also accommodate automatic equal OSPF cost on both ends of a network link, thus simplifying a network OSPF configuration. Automatic setting of OSPF cost using cost mirroring takes precedence over a local OSPF cost configuration.
To configure the interface cost under an area:

**Command syntax: cost-mirroring [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Note**

- No command return cost-mirroring to default state.

**Parameter table**

+-------------+--------------------------------+--------------+----------+
| Parameter   | Description                    | Range        | Default  |
+=============+================================+==============+==========+
| admin-state | Enable mirroring neighbor cost | | enabled    | disabled |
|             |                                | | disabled   |          |
+-------------+--------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
    dnRouter(cfg-ospf-area-if)# cost-mirroring enabled


**Removing Configuration**

To return cost-mirroring to its default value:
::

    dnRouter(cfg-protocols-ospf-area)# interface ge100-2/1/1

::

    dnRouter(cfg-ospf-area-if)# no cost-mirroring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
