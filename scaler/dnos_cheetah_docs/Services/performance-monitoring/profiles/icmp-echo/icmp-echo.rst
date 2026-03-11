services performance-monitoring profiles icmp-echo
--------------------------------------------------

**Minimum user role:** operator

To configure a ICMP echo IP performance measurement profile:

**Command syntax: icmp-echo [profile]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles

**Note**

- Up to 4 profiles may be configured in addition to the predefined `default` profile, the `default` profile can be updated but cannot be deleted.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                      | Range            | Default |
+===========+==================================================================================+==================+=========+
| profile   | The profile name. The profile is attached to a ICMP echo IP performance          | | string         | \-      |
|           | measurement session                                                              | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)#


**Removing Configuration**

To delete a certain profile:
::

    dnRouter(cfg-srv-pm-profiles)# no icmp-echo MyCustom_profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
