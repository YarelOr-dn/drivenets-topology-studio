services performance-monitoring profiles link-delay dscp-value
--------------------------------------------------------------

**Minimum user role:** operator

To set the DSCP value for transmitted packets:

**Command syntax: dscp-value [class-of-service]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| class-of-service | The DSCP value for reflected STAMP packets if dscp-handling-mode is set to       | 0-56  | 56      |
|                  | use-configured-value.                                                            |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# link-delay-measurement
    dnRouter(cfg-pm-profiles-link-delay)# profile MyCustom_profile
    dnRouter(cfg-profiles-link-delay-profile)# dscp-value 0


**Removing Configuration**

To return the DSCP value to default:
::

    dnRouter(cfg-profiles-link-delay-profile)# no dscp-value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
