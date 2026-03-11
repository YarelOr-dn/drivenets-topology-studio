system cprl cfm-oam
-------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the 802.1ag CFM OAM protocol:

**Command syntax: cfm-oam**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# cfm
    dnRouter(cfg-system-cprl-cfm)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the 802.1ag CFM OAM protocol:
::

    dnRouter(cfg-system-cprl)# no cfm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
