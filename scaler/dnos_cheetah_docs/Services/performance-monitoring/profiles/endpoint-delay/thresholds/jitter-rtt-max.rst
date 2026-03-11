services performance-monitoring profiles endpoint-delay thresholds jitter-rtt-max
---------------------------------------------------------------------------------

**Minimum user role:** operator

To set the maximum round trip jitter per test threshold:

**Command syntax: jitter-rtt-max [jitter-rtt-max]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay thresholds

**Parameter table**

+----------------+-------------------------------------------+------------+---------+
| Parameter      | Description                               | Range      | Default |
+================+===========================================+============+=========+
| jitter-rtt-max | Maximum jitter per test (in microseconds) | 1-60000000 | \-      |
+----------------+-------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-endpoint-delay-profile-thresholds)# jitter-rtt-max 1000


**Removing Configuration**

To remove the round trip jitter threshold:
::

    dnRouter(cfg-profiles-endpoint-delay-MyCustom_profile-thresholds)# no jitter-rtt-max

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
