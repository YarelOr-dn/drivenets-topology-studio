system cprl lldp burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the LLDP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl lldp

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 300     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# lldp
    dnRouter(cfg-system-cprl-lldp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the LLDP protocol:
::

    dnRouter(cfg-system-cprl-lldp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
