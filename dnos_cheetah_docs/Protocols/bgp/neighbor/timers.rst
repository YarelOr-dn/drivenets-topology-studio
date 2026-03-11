protocols bgp neighbor timers
-----------------------------

**Minimum user role:** operator

To adjust the interval at which BGP keep-alive and hold-time messages are sent to the neighbor or peer group:

**Command syntax: timers {keep-alive [keep-alive-timer], hold-time [hold-time-timer]}**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group

**Note**

- Setting the timer value to 0 disables the timer.

**Parameter table**

+------------------+------------------+------------+---------+
| Parameter        | Description      | Range      | Default |
+==================+==================+============+=========+
| keep-alive-timer | keep-alive-timer | 0-65535    | 60      |
+------------------+------------------+------------+---------+
| hold-time-timer  | hold-time-timer  | 0, 3-65535 | 180     |
+------------------+------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# timers keep-alive 30 hold-time 90

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# timers hold-time 100

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# timers hold-time 400 keep-alive 100


**Removing Configuration**

To revert all timers to their default values:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no timers

To revert the specified timer to its default value:
::

    dnRouter(cfg-protocols-bgp-group)# no timers keep-alive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
