protocols bgp neighbor-group passive
------------------------------------

**Minimum user role:** operator

In passive mode, the router will not initiate open messages to the peer. It will wait for the peer to issue an open request before a message is sent. To configure passive mode for a neighbor, peer group, or a neighbor in a peer group:

**Command syntax: passive [passive]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+-----------+----------------------------------------------------------------------------+--------------+----------+
| Parameter | Description                                                                | Range        | Default  |
+===========+============================================================================+==============+==========+
| passive   | Configure the router so that active open messages are not sent to the peer | | enabled    | disabled |
|           |                                                                            | | disabled   |          |
+-----------+----------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# passive enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# passive enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# passive enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# passive enabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# passive disabled


**Removing Configuration**

To remove passive mode:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no passive

::

    dnRouter(cfg-protocols-bgp-group)# no passive

::

    dnRouter(cfg-bgp-group-neighbor)# no passive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
