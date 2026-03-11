services performance-monitoring profiles endpoint-delay thresholds jitter-ingress-max
-------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the maximum destination to source jitter per test threshold:

**Command syntax: jitter-ingress-max [jitter-ingress-max]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+--------------------+-----------------------------------------------------------------+------------+---------+
| Parameter          | Description                                                     | Range      | Default |
+====================+=================================================================+============+=========+
| jitter-ingress-max | Maximum destination to source jitter per test (in microseconds) | 1-60000000 | \-      |
+--------------------+-----------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# jitter-ingress-max 800


**Removing Configuration**

To remove the ingress jitter threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no jitter-ingress-max

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
