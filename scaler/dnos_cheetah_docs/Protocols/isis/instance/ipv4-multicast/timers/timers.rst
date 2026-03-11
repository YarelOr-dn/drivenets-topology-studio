protocols isis instance address-family ipv4-multicast timers
------------------------------------------------------------

**Minimum user role:** operator

Enters address-family timers configuration level.

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# timers
    dnRouter(cfg-inst-afi-timers)#


**Removing Configuration**

To revert all timers configuration to default value:
::

    dnRouter(cfg-isis-inst-afi)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
