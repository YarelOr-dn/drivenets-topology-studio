network-services bridge-domain instance admin-state
---------------------------------------------------

**Minimum user role:** operator

Configure the Bridge-Domain Instance admin-state. Once disabled, the BD service is down, no traffic will flow

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Parameter table**

+-------------+---------------------------+--------------+---------+
| Parameter   | Description               | Range        | Default |
+=============+===========================+==============+=========+
| admin-state | Disable the Bridge Domain | | enabled    | enabled |
|             |                           | | disabled   |         |
+-------------+---------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-netsrv-bd-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
