system cprl efm
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the EFM protocol:

**Command syntax: efm**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# efm
    dnRouter(cfg-system-cprl-efm)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the EFM protocol:
::

    dnRouter(cfg-system-cprl)# no efm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
