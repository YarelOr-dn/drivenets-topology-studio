protocols bgp neighbor-group address-family maximum-prefix exceed-action
------------------------------------------------------------------------

**Minimum user role:** operator


To instruct BGP what action to take when the maximum allowed number of prefixes has been exceeded.

 - warning only - (Default behavior) maximum-prefix-number exceeded - restart the neighbor session. The session will restart after the restart-interval.
 - restart - maximum-prefix-number exceeded - restart the neighbor session. The session will restart after the restart-interval.

**Command syntax: exceed-action [action]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family maximum-prefix
- protocols bgp neighbor address-family maximum-prefix
- protocols bgp neighbor-group neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group address-family maximum-prefix
- network-services vrf instance protocols bgp neighbor-group neighbor address-family maximum-prefix

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- When the prefix number drops below the maximum prefix- number threshold, a clear message is sent.

**Parameter table**

+-----------+--------------------------------------------------------+------------------+--------------+
| Parameter | Description                                            | Range            | Default      |
+===========+========================================================+==================+==============+
| action    | action to be taken when maximum-prefix-number exceeded | | warning-only   | warning-only |
|           |                                                        | | restart        |              |
+-----------+--------------------------------------------------------+------------------+--------------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix
    dnRouter(cfg-neighbor-afi-maximum-prefix)# exceed-action warning-only


**Removing Configuration**

To revert to the default action (warning-only):
::

    dnRouter(cfg-neighbor-afi-maximum-prefix)# no exceed-action

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
