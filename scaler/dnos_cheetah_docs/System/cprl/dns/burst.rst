system cprl dns burst
---------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the DNS protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl dns

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
    dnRouter(cfg-system-cprl)# dns
    dnRouter(cfg-system-cprl-dns)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the DNS protocol:
::

    dnRouter(cfg-system-cprl-dns)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
