system cprl bfd burst
---------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the BFD protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl bfd

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 2000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# bfd
    dnRouter(cfg-system-cprl-bfd)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the BFD protocol:
::

    dnRouter(cfg-system-cprl-bfd)# no burst

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 10.0    | Command introduced                     |
+---------+----------------------------------------+
| 15.1    | Updated the default CPRL value for BFD |
+---------+----------------------------------------+
