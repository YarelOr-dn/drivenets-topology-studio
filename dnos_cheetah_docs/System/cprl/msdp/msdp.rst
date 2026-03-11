system cprl msdp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the MSDP protocol:

**Command syntax: msdp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# msdp
    dnRouter(cfg-system-cprl-msdp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the MSDP protocol:
::

    dnRouter(cfg-system-cprl)# no msdp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
