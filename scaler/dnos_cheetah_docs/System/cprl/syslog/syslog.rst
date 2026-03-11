system cprl syslog
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the Syslog protocol:

**Command syntax: syslog**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# syslog
    dnRouter(cfg-system-cprl-syslog)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the Syslog protocol:
::

    dnRouter(cfg-system-cprl)# no syslog

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
