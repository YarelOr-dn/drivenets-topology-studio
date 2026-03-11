system cprl ftp rate
--------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the FTP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ftp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 1000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ftp
    dnRouter(cfg-system-cprl-ftp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the FTP protocol:
::

    dnRouter(cfg-system-cprl-ftp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
