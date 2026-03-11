services performance-monitoring interface delay-measurement static-delay
------------------------------------------------------------------------

**Minimum user role:** operator

Configure the static delay for the interface. This delay may be signaled in routing protocol (example: isis) messages.

**Command syntax: static-delay [static-delay]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface delay-measurement

**Note**

- The delay is in the forward direction from the local interface to the remote interface.

**Parameter table**

+--------------+-------------------------------------+------------+---------+
| Parameter    | Description                         | Range      | Default |
+==============+=====================================+============+=========+
| static-delay | The Interface Delay in microseconds | 1-16777215 | \-      |
+--------------+-------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# static-delay 50
    dnRouter(cfg-pm-ge100-0/0/0-dm)#


**Removing Configuration**

To remove the delay, which will then no longer be signaled in the routing protocol (example: isis) messages.
::

    dnRouter(cfg-pm-ge100-0/0/0-dm)# no static-delay

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
