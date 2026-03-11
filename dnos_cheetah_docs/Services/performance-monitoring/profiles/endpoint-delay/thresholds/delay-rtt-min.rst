services performance-monitoring profiles endpoint-delay thresholds delay-rtt-min
--------------------------------------------------------------------------------

**Minimum user role:** operator

To set the minimum round trip delay per test threshold:

**Command syntax: delay-rtt-min [delay-rtt-min]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+---------------+----------------------------------------------------+------------+---------+
| Parameter     | Description                                        | Range      | Default |
+===============+====================================================+============+=========+
| delay-rtt-min | Minimum round trip time per test (in microseconds) | 1-60000000 | \-      |
+---------------+----------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# delay-rtt-min 1000


**Removing Configuration**

To remove the minimum round trip delay threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no delay-rtt-min

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
