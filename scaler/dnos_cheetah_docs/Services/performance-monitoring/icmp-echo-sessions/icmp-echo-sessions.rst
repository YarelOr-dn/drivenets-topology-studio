services performance-monitoring icmp-echo session
-------------------------------------------------

**Minimum user role:** operator

To configure a ICMP echo IP performance monitoring session:

**Command syntax: icmp-echo session [test-session]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring

**Parameter table**

+--------------+-------------+------------------+---------+
| Parameter    | Description | Range            | Default |
+==============+=============+==================+=========+
| test-session | a session   | | string         | \-      |
|              |             | | length 1-255   |         |
+--------------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)#


**Removing Configuration**

To remove a ICMP echo IP performance monitoring session:
::

    dnRouter(cfg-srv-pm)# no icmp-echo session Session-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
