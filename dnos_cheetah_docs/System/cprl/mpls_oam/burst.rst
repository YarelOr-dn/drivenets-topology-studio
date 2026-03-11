system cprl mpls-oam burst
--------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the MPLS-OAM protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl mpls-oam

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 300     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mpls-oam
    dnRouter(cfg-system-cprl-mpls-oam)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the MPLS-OAM protocol:
::

    dnRouter(cfg-system-cprl-mpls-oam)# no burst

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 10.0    | Command introduced                        |
+---------+-------------------------------------------+
| 15.0    | Command renamed from LSP-Ping to MPLS-OAM |
+---------+-------------------------------------------+
