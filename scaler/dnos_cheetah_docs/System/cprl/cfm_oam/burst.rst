system cprl cfm-oam burst
-------------------------

**Minimum user role:** operator

To set the burst limit of the control traffic to the 802.1ag CFM OAM protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl cfm-oam

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
    dnRouter(cfg-system-cprl)# cfm
    dnRouter(cfg-system-cprl-cfm)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the 802.1ag CFM OAM protocol:
::

    dnRouter(cfg-system-cprl-cfm)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
