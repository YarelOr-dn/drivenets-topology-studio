system cprl efm-oam
-------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the 802.3ah EFM OAM protocol:

**Command syntax: efm-oam**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# efm-oam
    dnRouter(cfg-system-cprl-efm-oam)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the 802.3ah EFM OAM protocol:
::

    dnRouter(cfg-system-cprl)# no efm-oam

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
