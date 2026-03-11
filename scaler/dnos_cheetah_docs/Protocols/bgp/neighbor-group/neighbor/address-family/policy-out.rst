protocols bgp neighbor-group neighbor address-family policy out
---------------------------------------------------------------

**Minimum user role:** operator

To apply a route map to a neighbor or peer group:

**Command syntax: policy [policy-out]** [, policy-out, policy-out] **out**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- If a policy is configured for a group, you cannot disable it for a neighbor within the group. You must explicitly set a different policy to achieve a different behavior from the group. You may even attach an empty policy.

- Can set multiple policies. In case multiple policies are set, policies are evaluated one after the other according to the user input order

- When setting a new policy, the policy will be appended to the existing attached policies

- To remove a policy, the user must specify the name of the policy to be remvoed

- To remove all policies, the user must specify all attached policy names

- To replace an attached policy, the user will need to first remove and than add a new policy. Can be performed in the same commit. the policy order imposes the functional behavior.

**Parameter table**

+------------+---------------------------------------+------------------+---------+
| Parameter  | Description                           | Range            | Default |
+============+=======================================+==================+=========+
| policy-out | applies the filter in outgoing routes | | string         | \-      |
|            |                                       | | length 1-255   |         |
+------------+---------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# policy MyPolicy out

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# policy MyPolicy out

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# policy GroupPolicy out
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# policy NeighborPolicy out

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# policy MyPolicy_1,MyPolicy_2 out


**Removing Configuration**

To disable the route map policy:
::

    dnRouter(cfg-bgp-group-afi)# no policy MyPolicy out

::

    dnRouter(cfg-bgp-neighbor-afi)# no policy MyPolicy out

::

    dnRouter(cfg-group-neighbor-afi)# no policy NeighborPolicy out

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 6.0     | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 11.0    | Added option to configure policy for a neighbor within a group |
+---------+----------------------------------------------------------------+
| 16.1    | Added support for multicast SAFI                               |
+---------+----------------------------------------------------------------+
| 17.2    | Added support for multiple policies attachments                |
+---------+----------------------------------------------------------------+
