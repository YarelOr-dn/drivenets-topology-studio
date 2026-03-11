protocols bgp address-family ipv6-vpn dampening
-----------------------------------------------

**Minimum user role:** operator

Route flapping is a condition in BGP in which a peer advertises that a route is available and then that the same route is unavailable within a short period of time. As a result, BGP excessively adds and removes routes from the forwarding table, increasing the processing load on the router.

Route flap dampening suppresses the advertisement of flapping routes until the route becomes more stable, thus reducing the number of advertisements sent between peers from flapping routers and increasing the stability of the BGP network.

To enable route flap dampening per address-family:

**Command syntax: dampening [admin-state]** half-life [half-life] reuse-threshold [reuse-threshold] suppress-threshold [suppress-threshold] max-suppress [max-suppress]

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-vpn
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn

**Note**

- The basic command (with no arguments) enables the feature with default values for the thresholds. You can configure different threshold values. The thresholds are listed in the Parameter table:

- This command is only applicable to unicast sub-address-families.

- Half-life, reuse-threshold, suppress-threshold, and max-suppress can only be configured for dampening enabled. When dampening is disabled, all optional parameters are set to their default value

- This option uses non-configurable default values for the following parameters:
- Max suppress penalty: 12000
- Min penalty: 375

**Parameter table**

+--------------------+---------------------------------------------------------------+--------------+----------+
| Parameter          | Description                                                   | Range        | Default  |
+====================+===============================================================+==============+==========+
| admin-state        | Enable route flap damping.                                    | | enabled    | disabled |
|                    |                                                               | | disabled   |          |
+--------------------+---------------------------------------------------------------+--------------+----------+
| half-life          | minutes                                                       | 1-45         | 15       |
+--------------------+---------------------------------------------------------------+--------------+----------+
| reuse-threshold    | Minimum penalty below which routes becomes reusable again     | 1-50000      | 750      |
+--------------------+---------------------------------------------------------------+--------------+----------+
| suppress-threshold | Maximum penalty above which route is suppressed by the device | 1-50000      | 2000     |
+--------------------+---------------------------------------------------------------+--------------+----------+
| max-suppress       | minutes                                                       | 1-255        | 60       |
+--------------------+---------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening enabled half-life 20 reuse-threshold 1000  suppress-threshold 1500 max-suppress 100

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening disabled half-life 30 reuse-threshold 550  suppress-threshold 1500 max-suppress 100

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening enabled reuse-threshold 1000


**Removing Configuration**

To revert to the default admin-state with all optional parameters set to their default values:
::

    dnRouter(cfg-protocols-bgp-afi)# no dampening

To revert to the thresholds to their default values:
::

    dnRouter(cfg-protocols-bgp-afi)# no dampening reuse-threshold 1000

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 7.0     | Command introduced                                    |
+---------+-------------------------------------------------------+
| 19.0    | Remove support for dampening in some address families |
+---------+-------------------------------------------------------+
