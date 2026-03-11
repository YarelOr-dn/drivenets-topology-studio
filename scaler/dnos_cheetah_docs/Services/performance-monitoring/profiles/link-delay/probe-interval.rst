services performance-monitoring profiles link-delay probe-interval
------------------------------------------------------------------

**Minimum user role:** operator

To set the interval between subsequent transmitted packets:

**Command syntax: probe-interval [probe-interval]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay

**Parameter table**

+----------------+-----------------------------------------+-------+---------+
| Parameter      | Description                             | Range | Default |
+================+=========================================+=======+=========+
| probe-interval | The interval between subsequent probes. | 1-255 | 3       |
+----------------+-----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# link-delay MyCustom_profile
    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# probe-interval 2


**Removing Configuration**

To revert the probe interval to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# no probe-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
