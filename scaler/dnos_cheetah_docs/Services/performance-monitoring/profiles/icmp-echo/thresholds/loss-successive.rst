services performance-monitoring profiles icmp-echo thresholds loss-successive
-----------------------------------------------------------------------------

**Minimum user role:** operator

To set the successive probe loss per test threshold:

**Command syntax: loss-successive [successive-loss]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo thresholds

**Parameter table**

+-----------------+-----------------------------------------------------+--------------+---------+
| Parameter       | Description                                         | Range        | Default |
+=================+=====================================================+==============+=========+
| successive-loss | Successive probe loss count indicating test failure | 0-4294967295 | \-      |
+-----------------+-----------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# thresholds
    dnRouter(cfg-profiles-icmp-echo-MyCustom_profile-thresholds)# loss-successive 5


**Removing Configuration**

To remove the successive loss threshold:
::

    dnRouter(cfg-profiles-icmp-echo-MyCustom_profile-thresholds)# no loss-successive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
