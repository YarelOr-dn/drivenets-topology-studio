services performance-monitoring profiles endpoint-delay
-------------------------------------------------------

**Minimum user role:** operator

To configure an endpoint delay measurement profile:

**Command syntax: endpoint-delay [profile]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles

**Note**

- Up to 4 profiles may be configured in addition to the predefined `default` profile, the `default` profile can be updated but cannot be deleted.

**Parameter table**

+-----------+---------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                         | Range            | Default |
+===========+=====================================================================+==================+=========+
| profile   | The profile name. The profile is attached to a Simple TWAMP session | | string         | \-      |
|           |                                                                     | | length 1-255   |         |
+-----------+---------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# endpoint-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-endpoint-delay-MyCustom_profile)#


**Removing Configuration**

To delete a certain profile:
::

    dnRouter(cfg-srv-pm-profiles)# no endpoint-delay MyCustom_profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
