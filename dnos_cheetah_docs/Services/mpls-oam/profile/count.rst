services mpls-oam profile count
-------------------------------

**Minimum user role:** operator

To configure the number of MPLS-OAM echo request packets that will be transmitted in a single test probe cycle:

**Command syntax: count [count]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Note**

- The total duration of the MPLS-OAM probe equals count x interval + 1 second. For example, if count = 3 and interval = 5, then the probe's total duration = 3x5+1 = 16 seconds. This in turn defines the rate at which probes are sent (in this example, every 16 seconds).

**Parameter table**

+-----------+--------------------------------+-----------+---------+
| Parameter | Description                    | Range     | Default |
+===========+================================+===========+=========+
| count     | mpls echo request packet count | 1-1000000 | 5       |
+-----------+--------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# count 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-mpls-oam-profile)# no count

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
