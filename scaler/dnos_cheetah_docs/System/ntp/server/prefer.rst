system ntp server vrf prefer
----------------------------

**Minimum user role:** operator

To enable an NTP server prefer:

**Command syntax: prefer**

**Command mode:** config

**Hierarchies**

- system ntp server vrf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 12.12.12.12 vrf default
    dnRouter(cfg-system-ntp-server)# prefer


**Removing Configuration**

To remove the specified NTP server prefer:
::

    dnRouter(cfg-system-ntp-server)# no prefer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
