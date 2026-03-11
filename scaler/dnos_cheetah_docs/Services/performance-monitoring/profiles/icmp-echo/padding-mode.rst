services performance-monitoring profiles icmp-echo padding-mode
---------------------------------------------------------------

**Minimum user role:** operator

To set the packet padding mode for the specified profile:

**Command syntax: padding-mode [mode]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Parameter table**

+-----------+-------------------------+------------+---------+
| Parameter | Description             | Range      | Default |
+===========+=========================+============+=========+
| mode      | The packet padding mode | | zero     | zero    |
|           |                         | | random   |         |
+-----------+-------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# padding-mode zero

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# padding-mode random


**Removing Configuration**

To revert to the padding-mode to its default value:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no padding-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
