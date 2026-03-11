system cprl micro-bfd
---------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Micro-BFD protocol:

**Command syntax: micro-bfd**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# micro-bfd
    dnRouter(cfg-system-cprl-micro-bfd)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Micro-BFD protocol:
::

    dnRouter(cfg-system-cprl)# no micro-bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
