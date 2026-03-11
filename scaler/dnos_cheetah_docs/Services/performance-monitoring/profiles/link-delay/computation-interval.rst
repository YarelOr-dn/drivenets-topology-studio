services performance-monitoring profiles link-delay computation-interval
------------------------------------------------------------------------

**Minimum user role:** operator

To set the periodic IP performance metrics computation interval:

**Command syntax: computation-interval [computation-interval]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay

**Parameter table**

+----------------------+--------------------------------+--------+---------+
| Parameter            | Description                    | Range  | Default |
+======================+================================+========+=========+
| computation-interval | Periodic computation interval. | 1-3600 | 30      |
+----------------------+--------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# link-delay MyCustom_profile
    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# computation-interval 300


**Removing Configuration**

To revert the computation interval to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# no computation-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
