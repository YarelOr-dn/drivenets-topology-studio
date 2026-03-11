services performance-monitoring profiles icmp-echo data-size
------------------------------------------------------------

**Minimum user role:** operator

To set the packet payload size value for transmitted packets:

**Command syntax: data-size [data-size]**

**Command mode:** config

**Hierarchies**

- services performance-monitoring profiles icmp-echo

**Note**

- The payload of transmitted packets contains in its data portion the 64-bytes of system-id, followed by padding to the data-size as specified by the user.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| data-size | Size of the Packet Payload. Suggested to run Path MTU Discovery to avoid packet  | 64-1400 | 64      |
|           | fragmentation in IPv4 and packet backholing in IPv6                              |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# performance-monitoring
    dnRouter(cfg-srv-pm)# profiles
    dnRouter(cfg-srv-pm-profiles)# icmp-echo MyCustom_profile
    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# data-size 100


**Removing Configuration**

To revert the packet payload size to its default value:
::

    dnRouter(cfg-pm-profiles-icmp-echo-MyCustom_profile)# no data-size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
