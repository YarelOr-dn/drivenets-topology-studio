services performance-monitoring profiles link-delay advertisement periodic interval
-----------------------------------------------------------------------------------

**Minimum user role:** operator

To set the periodic advertisement interval:

**Command syntax: interval [interval]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay advertisement periodic

**Parameter table**

+-----------+-------------------------------------------------+---------+---------+
| Parameter | Description                                     | Range   | Default |
+===========+=================================================+=========+=========+
| interval  | The interval between subsequent advertisements. | 30-3600 | 120     |
+-----------+-------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement periodic
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-adver-periodic)# interval 60


**Removing Configuration**

To revert the advertisement interval to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-adver-periodic)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
