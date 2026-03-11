services performance-monitoring icmp-echo session admin-state
-------------------------------------------------------------

**Minimum user role:** operator

To enable or disable a ICMP echo IP performance monitoring session:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring icmp-echo session

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | The administrative state of the ICMP echo IP perforamnce measurement             | | enabled    | disabled |
|             | test-session                                                                     | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-pm-icmp-echo-session)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
