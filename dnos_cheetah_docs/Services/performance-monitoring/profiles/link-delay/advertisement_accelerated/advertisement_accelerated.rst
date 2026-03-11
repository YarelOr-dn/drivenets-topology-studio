services performance-monitoring profiles link-delay advertisement accelerated
-----------------------------------------------------------------------------

**Minimum user role:** operator

To enter the accelerated advertisement configuration level for dynamic link delay measurement profiles:

**Command syntax: advertisement accelerated**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# dynamic-link-delay MyCustom_profile
    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# advertisement accelerated
    dnRouter(cfg-profiles-link-delay-MyCustom_profile-advertisement-accelerated)#


**Removing Configuration**

To revert accelerated advertisement configuration to default values:
::

    dnRouter(cfg-pm-profiles-link-delay-MyCustom_profile)# no advertisement accelerated

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
