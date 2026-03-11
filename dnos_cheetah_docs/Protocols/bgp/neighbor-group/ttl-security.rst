protocols bgp neighbor-group ttl-security
-----------------------------------------

**Minimum user role:** operator

Imposes eBGP TTL security per rfc5082.
When ttl-security is set for an EBGP neighbor, the following is expected for the given neighbor BGP IP/TCP session:
- Any egress packet is set with a TTL 255.
- Any ingress packet is checked for a TTL validity. Only packets with a TTL greater or equal to min-ttl are accepted, otherwise dropped.

The default system behavior is min-ttl = 255, imposing that eBGP neighbor must be directly connected (one hop apart).

Te user may impose a different min-ttl value to support the eBGP neighbors that are not directly connected.
In case min-ttl = 255 ttl-security keeps assumption of the eBGP neighbor being directly connected, regardless of the min-ttl value, as such:
- The neighbor address is expected to be a connected route.
- The egress interface is imposes per the neighbor address.
- In case BFD is requested, a single-hop BFD session is requested (unless a specific BFD-type is set).
In case min-ttl < 255 MH-EBGP session is assumed resulting:
- An update-source is required.
- The neighbor address is not bound to be a connected route.
- The egress interface is selected per the neighbor address routing solution.
- In case BFD is requested, a multi-hop BFD session is requested (unless a specific BFD-type is set).

**Command syntax: ttl-security [admin-state]** min-ttl [min-ttl]

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- The expected behavior is that both the BGP session sides are configured with ttl-security.

- Configuration is only valid for the eBGP neighbor. Commit validation is required (same as imposed for eBGP-multihop).

- Configuration is possible only with eBGP-multihop = 1. Commit validation is required.

- Applies for both IPv4 neighbors and IPv6 neighbors. The hop-count is handled instead of TTL for IPv6.

- When applied on a group, this property is inherited by all the group members. Applying this property on a neighbor within a group overrides the group settings.

- Neighbors within a neighbor-group derive the neighbor-group configuration (i.e has no default config) or can have a unique setting from the group.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enable ttl security for a given eBGP neighbor                                    | | enabled    | disabled |
|             |                                                                                  | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+
| min-ttl     | Allow received ttl lower than 255, the allowed received ttl will be              | 1-255        | 255      |
|             | greater-equal to (255-range)                                                     |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# ttl-security enabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP_GROUP
    dnRouter(cfg-protocols-bgp-group)# ttl-security enabled min-ttl 254

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP_GROUP
    dnRouter(cfg-protocols-bgp-group)# ttl-security enabled min-ttl 252
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-protocols-bgp-neighbor)# ttl-security enabled min-ttl 255


**Removing Configuration**

To revert configuration to default behavior the configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no ttl-security

To revert min-ttl to default behavior
::

    dnRouter(cfg-protocols-bgp-neighbor)# no ttl-security enabled min-ttl 255

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
