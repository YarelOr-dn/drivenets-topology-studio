protocols ospf instance area interface fast-reroute backup-candidate
--------------------------------------------------------------------

**Minimum user role:** operator

The command defines whether an OSPF interface will be included or excluded from being a candidate for repair path calculation.
When excluded, the interface will not be used for repair paths. The interface will be used for loop-free alternate calculations when the OSPF fast-reroute is globally enabled.

The behavior applies for both OSPF unicast fast-reroute and OSPF segment-routing based ti-fast-reroute (ti-lfa).
To define the administrative state of the fast reroute backup-candidate per OSPF interface:

**Command syntax: fast-reroute backup-candidate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | including or excluding an interface for being candidate for repair path          | | enabled    | \-      |
|             | calculation.                                                                     | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# area 0
    dnRouter(cfg-ospf-inst-area)# interface bundle-1
    dnRouter(cfg-inst-area-if)# fast-reroute backup-candidate enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-inst-area-if)# no fast-reroute backup-candidate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
