system cprl syslog burst
------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the Syslog protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl syslog

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 550     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# syslog
    dnRouter(cfg-system-cprl-syslog)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the Syslog protocol:
::

    dnRouter(cfg-system-cprl-syslog)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
