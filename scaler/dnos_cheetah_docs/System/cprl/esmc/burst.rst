system cprl esmc burst
----------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the SyncE ESMC protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl esmc

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
    dnRouter(cfg-system-cprl)# esmc
    dnRouter(cfg-system-cprl-esmc)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the SyncE ESMC protocol:
::

    dnRouter(cfg-system-cprl-esmc)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
