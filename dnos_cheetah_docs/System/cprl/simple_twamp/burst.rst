system cprl simple-twamp burst
------------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the Simple TWAMP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl simple-twamp

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
    dnRouter(cfg-system-cprl)# simple-twamp
    dnRouter(cfg-system-cprl-simple-twamp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the Simple TWAMP protocol:
::

    dnRouter(cfg-system-cprl-simple-twamp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
