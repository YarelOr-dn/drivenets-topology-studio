system cprl ftp burst
---------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the FTP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ftp

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
    dnRouter(cfg-system-cprl)# ftp
    dnRouter(cfg-system-cprl-ftp)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the FTP protocol:
::

    dnRouter(cfg-system-cprl-ftp)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
