services performance-monitoring simple-twamp session source-address
-------------------------------------------------------------------

**Minimum user role:** operator

To configure the source IP address for the Simple TWAMP monitoring session:

**Command syntax: source-address [ip-address]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring simple-twamp session

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
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)# source-address 1.1.1.1


**Removing Configuration**

To remove the configured source IP address:
::

    dnRouter(cfg-srv-pm-stamp-session)# no source-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
