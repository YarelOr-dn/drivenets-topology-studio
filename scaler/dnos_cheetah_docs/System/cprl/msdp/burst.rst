system cprl msdp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the MSDP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl msdp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 800     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# msdp
    dnRouter(cfg-system-cprl-msdp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the MSDP protocol:
::

    dnRouter(cfg-system-cprl-msdp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
