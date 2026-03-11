services performance-monitoring profiles icmp-echo ip-ttl
---------------------------------------------------------

**Minimum user role:** operator

To set the IP TTL value for transmitted packets:

**Command syntax: ip-ttl [ip-ttl]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Parameter table**

+-----------+----------------------------------------------+-------+---------+
| Parameter | Description                                  | Range | Default |
+===========+==============================================+=======+=========+
| ip-ttl    | Set the IP TTL value for transmitted packets | 1-255 | 255     |
+-----------+----------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# ip-ttl 60


**Removing Configuration**

To return the IP TTL value to default:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no ip-ttl

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
