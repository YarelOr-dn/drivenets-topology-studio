protocols isis instance address-family ipv4-multicast fast-reroute backup-candidate
-----------------------------------------------------------------------------------

**Minimum user role:** operator

This commands supports including or excluding all IS-IS instance interfaces for being a candidate for repair path calculations.
When excluded, the interface will not be used for repair paths.
The interface will be used for loop-free alternate calculations when IS-IS fast-reroute is globally enabled.


**Command syntax: fast-reroute backup-candidate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-multicast

**Parameter table**

+-------------+---------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                     | Range        | Default |
+=============+=================================================================================+==============+=========+
| admin-state | Enable interface for being candidate for repair path calculation for L2 routing | | enabled    | enabled |
|             |                                                                                 | | disabled   |         |
+-------------+---------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# fast-reroute backup-candidate enabled


**Removing Configuration**

To revert fast-reroute backup-candidate settings to their default value:
::

    dnRouter(cfg-isis-inst-afi)# no fast-reroute backup-candidate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
