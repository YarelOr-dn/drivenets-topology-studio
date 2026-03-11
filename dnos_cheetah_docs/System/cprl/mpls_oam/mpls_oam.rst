system cprl mpls-oam
--------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the MPLS-OAM protocol:

**Command syntax: mpls-oam**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mpls-oam
    dnRouter(cfg-system-cprl-mpls-oam)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the MPLS-OAM protocol:
::

    dnRouter(cfg-system-cprl)# no mpls-oam

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 10.0    | Command introduced                        |
+---------+-------------------------------------------+
| 15.0    | Command renamed from LSP-Ping to MPLS-OAM |
+---------+-------------------------------------------+
