system cprl twamp
-----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the TWAMP protocol:

**Command syntax: twamp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# twamp
    dnRouter(cfg-system-cprl-twamp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the TWAMP protocol:
::

    dnRouter(cfg-system-cprl)# no twamp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
