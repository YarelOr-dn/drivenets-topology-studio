system cprl pcep burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the PCEP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl pcep

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
    dnRouter(cfg-system-cprl)# pcep
    dnRouter(cfg-system-cprl-pcep)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the PCEP protocol:
::

    dnRouter(cfg-system-cprl-pcep)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
