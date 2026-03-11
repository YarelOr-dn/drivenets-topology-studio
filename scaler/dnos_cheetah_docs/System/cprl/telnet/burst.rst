system cprl telnet burst
------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the Telnet protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl telnet

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 1000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# telnet
    dnRouter(cfg-system-cprl-telnet)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the Telnet protocol:
::

    dnRouter(cfg-system-cprl-telnet)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
