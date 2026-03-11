services performance-monitoring icmp-echo session source-address
----------------------------------------------------------------

**Minimum user role:** operator

To configure the source IP address for the ICMP echo IP performance monitoring session:

**Command syntax: source-address [ip-address]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring icmp-echo session

**Parameter table**

+------------+-------------------+--------------+---------+
| Parameter  | Description       | Range        | Default |
+============+===================+==============+=========+
| ip-address | Sender IP address | | A.B.C.D    | \-      |
|            |                   | | X:X::X:X   |         |
+------------+-------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# source-address 1.1.1.1


**Removing Configuration**

To remove the configured source IP address:
::

    dnRouter(cfg-srv-pm-icmp-echo-session)# no source-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
