services performance-monitoring profiles icmp-echo dscp-value
-------------------------------------------------------------

**Minimum user role:** operator

To set the DSCP value for transmitted packets:

**Command syntax: dscp-value [class-of-service]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Parameter table**

+------------------+-----------------------------------------+-------+---------+
| Parameter        | Description                             | Range | Default |
+==================+=========================================+=======+=========+
| class-of-service | The DSCP value for transmitted packets. | 0-56  | 48      |
+------------------+-----------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# dscp-value 0


**Removing Configuration**

To return the DSCP value to default:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no dscp-value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
