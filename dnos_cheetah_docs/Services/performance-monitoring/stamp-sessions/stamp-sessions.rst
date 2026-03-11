services performance-monitoring simple-twamp session
----------------------------------------------------

**Minimum user role:** operator

To configure a Simple TWAMP monitoring session:

**Command syntax: simple-twamp session [test-session]**

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
    dnRouter(cfg-srv-pm)# simple-twamp session Session-1
    dnRouter(cfg-srv-pm-stamp-session)#


**Removing Configuration**

To remove a Simple TWAMP monitoring session:
::

    dnRouter(cfg-srv-pm)# no simple-twamp session Session-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
