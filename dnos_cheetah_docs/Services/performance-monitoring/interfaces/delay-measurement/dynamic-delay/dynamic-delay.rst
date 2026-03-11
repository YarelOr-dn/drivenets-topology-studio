services performance-monitoring interface delay-measurement dynamic-delay
-------------------------------------------------------------------------

**Minimum user role:** operator

To configure dynamic link delay measurement on an interface:

**Command syntax: dynamic-delay**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface delay-measurement

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# dynamic-delay
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)#


**Removing Configuration**

To remove the dynamic link delay session on the interface:
::

    dnRouter(cfg-pm-ge100-0/0/0-dm)# no dynamic-delay

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 18.0    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
