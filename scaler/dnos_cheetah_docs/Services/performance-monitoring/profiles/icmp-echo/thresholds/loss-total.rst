services performance-monitoring profiles icmp-echo thresholds loss-total
------------------------------------------------------------------------

**Minimum user role:** operator

To set the total probe loss per test threshold:

**Command syntax: loss-total [total-loss]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo thresholds

**Parameter table**

+------------+------------------------------------------------+--------------+---------+
| Parameter  | Description                                    | Range        | Default |
+============+================================================+==============+=========+
| total-loss | Total probe loss count indicating test failure | 0-4294967295 | \-      |
+------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-profile)# thresholds
    dnRouter(cfg-profiles-icmp-echo-MyCustom_profile-thresholds)# loss-total 10


**Removing Configuration**

To remove the total loss threshold:
::

    dnRouter(cfg-profiles-icmp-echo-MyCustom_profile-thresholds)# no loss-total

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
