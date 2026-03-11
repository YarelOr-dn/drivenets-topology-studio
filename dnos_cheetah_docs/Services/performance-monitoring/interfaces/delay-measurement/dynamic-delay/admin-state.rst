services performance-monitoring interface delay-measurement dynamic-delay admin-state
-------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable a dynamic link delay monitoring session on an interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring interface delay-measurement dynamic-delay

**Parameter table**

+-------------+-------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                 | Range        | Default  |
+=============+=============================================================+==============+==========+
| admin-state | Enable or disable the dynamic link delay monitoring session | | enabled    | disabled |
|             |                                                             | | disabled   |          |
+-------------+-------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# dynamic-delay
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# admin-state enabled
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)#

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# interface ge100-0/0/0
    dnRouter(cfg-srv-pm-ge100-0/0/0)# delay-measurement
    dnRouter(cfg-pm-ge100-0/0/0-dm)# dynamic-delay
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# admin-state disabled
    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)#


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-ge100-0/0/0-dm-dynamic-delay)# no admin-state

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 18.0    | Command introduced                 |
+---------+------------------------------------+
| 18.2    | removed the 'interfaces' hierarchy |
+---------+------------------------------------+
