system cprl mac-unresolved
--------------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the MAC-Unresolved protocol:

**Command syntax: mac-unresolved**

**Command mode:** config

**Hierarchies**

- system cprl

**Note**

- MAC-Unresolved refers to packets punted to CPU due to unresolved destination MAC address.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mac-unresolved
    dnRouter(cfg-system-cprl-mac-unresolved)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the MAC-Unresolved protocol:
::

    dnRouter(cfg-system-cprl)# no mac-unresolved

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 10.0    | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 16.1    | Control protocol renamed from ARP-Unresolved to MAC-Unresolved |
+---------+----------------------------------------------------------------+
