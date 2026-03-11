system cprl esmc
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the SyncE ESMC protocol:

**Command syntax: esmc**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# esmc
    dnRouter(cfg-system-cprl-esmc)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the SyncE ESMC protocol:
::

    dnRouter(cfg-system-cprl)# no esmc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
