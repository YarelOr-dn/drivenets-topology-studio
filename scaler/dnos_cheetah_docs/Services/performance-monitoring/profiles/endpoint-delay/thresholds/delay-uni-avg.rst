services performance-monitoring profiles endpoint-delay thresholds delay-unidirectional-avg
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the average unidirectional delay per test threshold:

**Command syntax: delay-unidirectional-avg [delay-unidirectional-avg]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+--------------------------+--------------------------------------------------------------+------------+---------+
| Parameter                | Description                                                  | Range      | Default |
+==========================+==============================================================+============+=========+
| delay-unidirectional-avg | Average unidirectional delay time per test (in microseconds) | 1-60000000 | \-      |
+--------------------------+--------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# delay-unidirectional-avg 1000


**Removing Configuration**

To remove the average unidirectional delay threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no delay-unidirectional-avg

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
