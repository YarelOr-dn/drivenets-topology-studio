system cprl mpls-oam rate
-------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the MPLS-OAM protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl mpls-oam

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 250     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mpls-oam
    dnRouter(cfg-system-cprl-mpls-oam)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the MPLS-OAM protocol:
::

    dnRouter(cfg-system-cprl-mpls-oam)# no rate

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 10.0    | Command introduced                        |
+---------+-------------------------------------------+
| 15.0    | Command renamed from LSP-Ping to MPLS-OAM |
+---------+-------------------------------------------+
