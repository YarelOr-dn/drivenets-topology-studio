services twamp data-destination-port
------------------------------------

**Minimum user role:** operator

The destination port is the incoming UDP port that the data connection uses to send data packets to the TWAMP server.

By default, the UDP data destination port range is between 10000-20000. You can configure a smaller port range within this range.

To configure the destination port range:

**Command syntax: data-destination-port [data-dst-ports]**

**Command mode:** config

**Hierarchies**

- services twamp

**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                      | Range       | Default |
+================+==================================================================================+=============+=========+
| data-dst-ports | Minimal value of the UDP destination port range. Maximal value of the UDP        | 10000-20000 | 10000   |
|                | destination port range.                                                          |             |         |
+----------------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp
    dnRouter(cfg-srv-twamp)# data-destination-port 10000-11000
    dnRouter(cfg-srv-twamp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp)# no data-destination-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
