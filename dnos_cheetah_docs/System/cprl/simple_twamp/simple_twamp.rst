system cprl simple-twamp
------------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Simple TWAMP protocol:

**Command syntax: simple-twamp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# simple-twamp
    dnRouter(cfg-system-cprl-simple-twamp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Simple TWAMP protocol:
::

    dnRouter(cfg-system-cprl)# no simple-twamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
