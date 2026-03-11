network-services vrf instance protocols bgp neighbor-group minimum-hold-time
----------------------------------------------------------------------------

**Minimum user role:** operator

To adjust the threshold for the minimum-hold-time:

**Command syntax: minimum-hold-time [minimum-hold-time]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor

**Note**

- The value of the set minimum-hold-time must be less or equal to the hold-time set value.

**Parameter table**

+-------------------+-------------------+---------+---------+
| Parameter         | Description       | Range   | Default |
+===================+===================+=========+=========+
| minimum-hold-time | minimum-hold-time | 3-65535 | 3       |
+-------------------+-------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# minimum-hold-time 7

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# minimum-hold-time 11


**Removing Configuration**

To revert minimum-hold-time value to their default values:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no minimum-hold-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
