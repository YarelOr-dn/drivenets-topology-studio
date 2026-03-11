services performance-monitoring profiles link-delay advertisement periodic delay-change-threshold microseconds
--------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the minimum delay change in microseconds required for periodic advertisements:

**Command syntax: delay-change-threshold microseconds [minimum-change-microseconds]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay advertisement periodic

**Parameter table**

+-----------------------------+------------------------------------------------+----------+---------+
| Parameter                   | Description                                    | Range    | Default |
+=============================+================================================+==========+=========+
| minimum-change-microseconds | Set the delay change threshold in microseconds | 1-100000 | 1000    |
+-----------------------------+------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement periodic
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-periodic)# delay-change-threshold microseconds 2000


**Removing Configuration**

To revert the minimum delay change threshold to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-periodic)# no delay-change-threshold

To return the microseconds threshold configuration to default:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-periodic)# no delay-change-threshold microseconds

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
