services performance-monitoring profiles endpoint-delay thresholds
------------------------------------------------------------------

**Minimum user role:** operator

To configure IP performance monitoring thresholds:

**Command syntax: thresholds**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)#


**Removing Configuration**

To remove the IP performance monitoring thresholds:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no thresholds

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
