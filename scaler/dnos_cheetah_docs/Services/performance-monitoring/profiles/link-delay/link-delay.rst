services performance-monitoring profiles link-delay
---------------------------------------------------

**Minimum user role:** operator

To configure a dynamic link delay measurement profile:

**Command syntax: link-delay [profile]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles

**Note**

- Up to 5 profiles may be configured.

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
    dnRouter(cfg-srv-pm-profiles)# link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)#


**Removing Configuration**

To delete a certain profile:
::

    dnRouter(cfg-pm-profiles)# no link-delay MyCustom_profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
