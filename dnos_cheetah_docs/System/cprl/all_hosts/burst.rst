system cprl all-hosts burst
---------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for all hosts:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl all-hosts

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
    dnRouter(cfg-system-cprl)# all-hosts
    dnRouter(cfg-system-cprl-all-hosts)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value:
::

    dnRouter(cfg-system-cprl-all-hosts)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
