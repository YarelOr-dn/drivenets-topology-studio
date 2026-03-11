protocols ospf instance fast-reroute backup-candidate
-----------------------------------------------------

**Minimum user role:** operator

The command defines whether all OSPF interfaces will be included or excluded from being a candidate for repair path calculation.
When excluded, the interfaces will not be used for repair paths. The interfaces will be used for loop-free alternate calculations when the OSPF fast-reroute is globally enabled.

The behavior applies for both OSPF unicast fast-reroute and OSPF segment-routing based ti-fast-reroute (ti-lfa).
To define the administrative state of fast reroute backup-candidate per all OSPF interfaces:

**Command syntax: fast-reroute backup-candidate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | including or excluding all interfaces for being candidate for repair path        | | enabled    | enabled |
|             | calculation. Used as default behavior for all interfaces, unless more specific   | | disabled   |         |
|             | config exist                                                                     |              |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# fast-reroute backup-candidate enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-protocols-ospf-inst)# no fast-reroute backup-candidate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
