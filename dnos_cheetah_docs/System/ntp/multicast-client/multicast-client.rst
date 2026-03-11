system ntp multicast-client vrf
-------------------------------

**Minimum user role:** operator

To configure an NTP multicast client:

**Command syntax: multicast-client vrf [multicast-client]**

**Command mode:** config

**Hierarchies**

- system ntp

**Parameter table**

+------------------+---------------------+------------------+---------+
| Parameter        | Description         | Range            | Default |
+==================+=====================+==================+=========+
| multicast-client | The name of the vrf | | string         | \-      |
|                  |                     | | length 1-255   |         |
+------------------+---------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# multicast-client vrf default


**Removing Configuration**

To remove the specified NTP multicast client:
::

    dnRouter(cfg-system-ntp)# no multicast-client vrf default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
