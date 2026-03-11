services mpls-oam profile interval
----------------------------------

**Minimum user role:** operator


MPLS-OAM sends MPLS echo requests periodically. You can set an interval between packets within the probe.

To configure the interval between consecutive MPLS echo requests:

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Note**

- The total duration of the MPLS-OAM probe equals count x interval + 1 second. For example, if count = 3 and interval = 5, then the probe's total duration = 3x5+1 = 16 seconds. This in turn defines the rate at which probes are sent (in this example, every 16 seconds).

**Parameter table**

+-----------+-----------------------------------+---------+---------+
| Parameter | Description                       | Range   | Default |
+===========+===================================+=========+=========+
| interval  | mpls echo request packet interval | 2-86400 | 5       |
+-----------+-----------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# interval 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-mpls-oam-profile)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
