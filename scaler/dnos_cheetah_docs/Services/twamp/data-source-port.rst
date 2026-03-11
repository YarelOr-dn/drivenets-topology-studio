services twamp data-source-port
-------------------------------

**Minimum user role:** operator

The source port is the incoming UDP port that the data connection uses to send data packets to the TWAMP server.

By default, the UDP data source port range is between 10000-20000. You can configure a smaller port range within this range.

To configure the source port range:

**Command syntax: data-source-port [data-src-ports]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| data-src-ports | Minimal value of the UDP source port range. Maximal value of the UDP source port | 10000-20000 | 10000   |
|                | range.                                                                           |             |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# data-source-port 10000-11000
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp)# no data-source-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
