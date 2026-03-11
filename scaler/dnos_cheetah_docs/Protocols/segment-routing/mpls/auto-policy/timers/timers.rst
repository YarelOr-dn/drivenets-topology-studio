protocols segment-routing mpls auto-policy timers
-------------------------------------------------

**Minimum user role:** operator

To enter the SR-TE auto policy global timers configuration hierarchy:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# timers
    dnRouter(cfg-mpls-auto-policy-timers)#


**Removing Configuration**

To remove all configured auto-policy global timers configuration to default:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
