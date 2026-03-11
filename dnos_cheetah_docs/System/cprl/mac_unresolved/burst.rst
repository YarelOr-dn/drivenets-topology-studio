system cprl mac-unresolved burst
--------------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the MAC-Unresolved protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl mac-unresolved

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 50      |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# mac-unresolved
    dnRouter(cfg-system-cprl-mac-unresolved)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the MAC-Unresolved protocol:
::

    dnRouter(cfg-system-cprl-mac-unresolved)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
