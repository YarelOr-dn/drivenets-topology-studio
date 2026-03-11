services performance-monitoring profiles link-delay advertisement periodic delay-change-threshold percentages
-------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the minimum delay change in percentages required for periodic advertisements:

**Command syntax: delay-change-threshold percentages [minimum-change-percentages]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay advertisement periodic

**Parameter table**

+----------------------------+-----------------------------------------------+-------+---------+
| Parameter                  | Description                                   | Range | Default |
+============================+===============================================+=======+=========+
| minimum-change-percentages | Set the delay change threshold in percentages | 5-100 | 10      |
+----------------------------+-----------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement periodic
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-periodic)# delay-change-threshold percentages 10


**Removing Configuration**

To revert the minimum delay change threshold to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-adver-periodic)# no delay-change-threshold

To return the percentages threshold configuration to default:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-periodic)# no delay-change-threshold percentages

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
