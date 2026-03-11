services performance-monitoring profiles endpoint-delay thresholds jitter-egress-max
------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the maximum source to destination jitter per test threshold:

**Command syntax: jitter-egress-max [jitter-egress-max]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+-------------------+-----------------------------------------------------------------+------------+---------+
| Parameter         | Description                                                     | Range      | Default |
+===================+=================================================================+============+=========+
| jitter-egress-max | Maximum source to destination jitter per test (in microseconds) | 1-60000000 | \-      |
+-------------------+-----------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-profile-thresholds)# jitter-egress-max 800


**Removing Configuration**

To remove the egress jitter threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no jitter-egress-max

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
