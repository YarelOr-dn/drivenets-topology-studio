services performance-monitoring profiles endpoint-delay thresholds delay-unidirectional-max
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the maximum unidirectional delay per test threshold:

**Command syntax: delay-unidirectional-max [delay-unidirectional-max]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+--------------------------+--------------------------------------------------------------+------------+---------+
| Parameter                | Description                                                  | Range      | Default |
+==========================+==============================================================+============+=========+
| delay-unidirectional-max | Maximum unidirectional delay time per test (in microseconds) | 1-60000000 | \-      |
+--------------------------+--------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# delay-unidirectional-max 2000


**Removing Configuration**

To remove the maximum unidirectional delay threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no delay-unidirectional-max

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
