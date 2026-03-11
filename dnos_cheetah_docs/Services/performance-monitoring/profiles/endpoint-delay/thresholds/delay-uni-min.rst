services performance-monitoring profiles endpoint-delay thresholds delay-unidirectional-min
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the minimum unidirectional delay per test threshold:

**Command syntax: delay-unidirectional-min [delay-unidirectional-min]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+--------------------------+--------------------------------------------------------------+------------+---------+
| Parameter                | Description                                                  | Range      | Default |
+==========================+==============================================================+============+=========+
| delay-unidirectional-min | Minimum unidirectional delay time per test (in microseconds) | 1-60000000 | \-      |
+--------------------------+--------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# delay-unidirectional-min 900


**Removing Configuration**

To remove the minimum unidirectional delay threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no delay-unidirectional-min

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
