services performance-monitoring profiles link-delay advertisement accelerated admin-state
-----------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable the accelerated advertisement for the dynamic link delay profile:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay advertisement accelerated

**Parameter table**

+-------------+-------------------------------------------------+--------------+----------+
| Parameter   | Description                                     | Range        | Default  |
+=============+=================================================+==============+==========+
| admin-state | Enable or disable the accelerated advertisement | | enabled    | disabled |
|             |                                                 | | disabled   |          |
+-------------+-------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement periodic
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-accelerated)# admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement periodic
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-accelerated)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-accelerated)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
