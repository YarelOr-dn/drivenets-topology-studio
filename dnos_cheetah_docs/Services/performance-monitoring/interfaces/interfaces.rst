services performance-monitoring interface
-----------------------------------------

**Minimum user role:** operator

Configure the interface to which the Performance Monitoring shall be applied.

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring

**Note**

- support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y>

**Parameter table**

+-----------+-------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                 | Range            | Default |
+===========+=============================================================+==================+=========+
| interface | The name of the interface -- used to address the interface. | | string         | \-      |
|           |                                                             | | length 1-255   |         |
+-----------+-------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface bundle-1
    dnRouter(cfg-srv-pm-bundle-1)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0.1
    dnRouter(cfg-srv-pm-ge100-0/0/0.1)#


**Removing Configuration**

To remove performance monitoring configuration on a specifice interface
::

    dnRouter(cfg-srv-pm)# no interface ge100-0/0/0

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 16.1    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
