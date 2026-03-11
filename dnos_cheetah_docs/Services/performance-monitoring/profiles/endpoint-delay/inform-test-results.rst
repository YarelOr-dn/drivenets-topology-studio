services performance-monitoring profiles endpoint-delay inform-test-results
---------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable the generation of test failure system events for the specified profile:

**Command syntax: inform-test-results [admin-state]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles endpoint-delay

**Parameter table**

+-------------+-------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                       | Range        | Default  |
+=============+===================================================================+==============+==========+
| admin-state | Enable or diable the generation of the test failure system event. | | enabled    | disabled |
|             |                                                                   | | disabled   |          |
+-------------+-------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# inform-test-results enabled

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# inform-test-results disabled


**Removing Configuration**

To revert to the inform-test-results configuration to its default value:
::

    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)# no inform-test-results

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
