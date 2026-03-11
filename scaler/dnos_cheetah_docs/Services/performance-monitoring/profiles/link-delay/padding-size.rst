services performance-monitoring profiles link-delay padding-size
----------------------------------------------------------------

**Minimum user role:** operator

To set the packet padding size value for transmitted packets:

**Command syntax: padding-size [packet-padding-size]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles link-delay

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter           | Description                                                                      | Range   | Default |
+=====================+==================================================================================+=========+=========+
| packet-padding-size | Size of the Packet Padding. Suggested to run Path MTU Discovery to avoid packet  | 60-1400 | 60      |
|                     | fragmentation in IPv4 and packet backholing in IPv6                              |         |         |
+---------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# link-delay MyCustom_profile
    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# padding-size 100


**Removing Configuration**

To revert the packet padding size to its default value:
::

    dnRouter(cfg-profiles-link-delay-MyCustom_profile)# no padding-size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
