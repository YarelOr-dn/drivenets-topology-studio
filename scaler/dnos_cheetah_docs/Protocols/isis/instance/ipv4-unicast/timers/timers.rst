protocols isis instance address-family ipv4-unicast timers
----------------------------------------------------------

**Minimum user role:** operator

Enters address-family timers configuration level.

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
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
| 9.0     | Command introduced |
+---------+--------------------+
