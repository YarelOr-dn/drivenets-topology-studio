system cprl bfd
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the BFD protocol:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# bfd
    dnRouter(cfg-system-cprl-bfd)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the BFD protocol:
::

    dnRouter(cfg-system-cprl)# no bfd

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 10.0    | Command introduced                     |
+---------+----------------------------------------+
| 15.1    | Updated the default CPRL value for BFD |
+---------+----------------------------------------+
