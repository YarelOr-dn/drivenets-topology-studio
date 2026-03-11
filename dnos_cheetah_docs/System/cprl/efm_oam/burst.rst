system cprl efm-oam burst
-------------------------

**Minimum user role:** operator

To set the burst limit of the control traffic to the 802.3ah EFM OAM protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl efm-oam

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 1000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# efm-oam
    dnRouter(cfg-system-cprl-efm-oam)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the 802.3ah EFM OAM protocol:
::

    dnRouter(cfg-system-cprl-efm-oam)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
