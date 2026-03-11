system cprl pcep
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the PCEP protocol:

**Command syntax: pcep**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# pcep
    dnRouter(cfg-system-cprl-pcep)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the PCEP protocol:
::

    dnRouter(cfg-system-cprl)# no pcep

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
