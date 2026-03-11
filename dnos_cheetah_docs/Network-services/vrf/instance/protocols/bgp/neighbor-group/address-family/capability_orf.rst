network-services vrf instance protocols bgp neighbor-group address-family capability orf
----------------------------------------------------------------------------------------

**Minimum user role:** operator

This command instructs the BGP router whether or not to establish a peering session with a neighbor that does not support capability negotiation, neighbors that are members of a peer group, or with a neighbor in a peer group. To configure this option:

**Command syntax: capability orf [capability-orf]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- This command cannot be enabled with the strict-capability-match configuration. See "bgp neighbor strict-capability-match"

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+----------+
| Parameter      | Description                                                                      | Range            | Default  |
+================+==================================================================================+==================+==========+
| capability-orf | Advertises outbound route filter (ORF) capabilities to peer routers enabled -    | | enabled        | disabled |
|                | enables the ORF prefix list capability in both receive and send mode             | | disabled       |          |
|                | receive-only - enables the ORF prefix list capability in receive mode only       | | send-only      |          |
|                | send-only - enables the ORF prefix list capability in send mode only disabled -  | | receive-only   |          |
|                | disables ORF capability                                                          |                  |          |
+----------------+----------------------------------------------------------------------------------+------------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# capability orf enabled
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group GROUP_1
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# capability orf receive-only
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-group-neighbor-afi)# capability orf send-only
    dnRouter(cfg-protocols-bgp-group)# neighbor 2.2.2.2
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-group-neighbor-afi)# capability orf disabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-group-afi)# no capability orf

::

    dnRouter(cfg-bgp-neighbor-afi)# no capability orf

::

    dnRouter(cfg-group-neighbor-afi)# no capability orf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
