services performance-monitoring profiles icmp-echo thresholds
-------------------------------------------------------------

**Minimum user role:** operator

To configure IP performance monitoring thresholds:

**Command syntax: thresholds**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-icmp-echo-MyCustom_profile-thresholds)#


**Removing Configuration**

To remove the IP performance monitoring thresholds:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no thresholds

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
