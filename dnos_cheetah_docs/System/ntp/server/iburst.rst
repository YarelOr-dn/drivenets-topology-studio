system ntp server vrf iburst
----------------------------

**Minimum user role:** operator

To enable an NTP server iburst:

**Command syntax: iburst**

**Command mode:** config

**Hierarchies**

- system ntp server vrf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 12.12.12.12 vrf default
    dnRouter(cfg-system-ntp-server)# iburst


**Removing Configuration**

To remove the specified NTP server iburst:
::

    dnRouter(cfg-system-ntp-server)# no iburst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
