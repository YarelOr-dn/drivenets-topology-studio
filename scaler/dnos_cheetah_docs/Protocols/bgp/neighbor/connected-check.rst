protocols bgp neighbor connected-check
--------------------------------------

**Minimum user role:** operator

Typically in eBGP peering, a check is done to confirm that the neighbor is listed in the routing table as being directly connected. eBGP peering will not be attempted with a neighbor that is not directly connected. When the loopback interface is used for peering, then the IP address of the neighbor will not be listed as being directly connected and so peering will not be possible.

The following command instructs the BGP router whether or not to disable the connection verification check for eBGP peering sessions that are directly connected but are configured on a loopback interface or with a non-directly connected IP address.

**Command syntax: connected-check [connected-check]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- The option to disable the check is required only when the neighbor ebgp-multihop command is configured with a TTL value of 1. See "bgp neighbor ebgp-multihop".

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter       | Description                                                                      | Range        | Default |
+=================+==================================================================================+==============+=========+
| connected-check | disable the connection verification process for eBGP peering sessions that are   | | enabled    | enabled |
|                 | reachable by a single hop but are configured on a loopback interface or          | | disabled   |         |
|                 | otherwise configured with a non-directly connected IP address                    |              |         |
+-----------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# connected-check disabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# connected-check disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# connected-check disabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# connected-check enabled


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-protocols-bgp-group)# no connected-check

::

    dnRouter(cfg-protocols-bgp-neighbor)# no connected-check

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
