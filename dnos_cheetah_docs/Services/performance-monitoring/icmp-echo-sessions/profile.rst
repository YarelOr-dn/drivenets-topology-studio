services performance-monitoring icmp-echo session profile
---------------------------------------------------------

**Minimum user role:** operator

To associate a configuration profile for the ICMP echo IP performance monitoring session:

**Command syntax: profile [profile-name]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring icmp-echo session

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter    | Description                                                                      | Range            | Default |
+==============+==================================================================================+==================+=========+
| profile-name | The ICMP echo IP perforamnce measurement profile containing session parameters   | | string         | default |
|              | configuration                                                                    | | length 1-255   |         |
+--------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# icmp-echo session Session-1
    dnRouter(cfg-srv-pm-icmp-echo-session)# profile Daily-Monitoring


**Removing Configuration**

To revert to the default configuration profile for the ICMP echo IP performance monitoring session:
::

    dnRouter(cfg-srv-pm-icmp-echo-session)# no profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
