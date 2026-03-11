network-services vpws instance pw admin-state
---------------------------------------------

**Minimum user role:** operator

Configure the Pseudowire admin-state. Once disabled, no Pseudowire is signaled and the VPWS service is down:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+-------------+--------------------+--------------+---------+
| Parameter   | Description        | Range        | Default |
+=============+====================+==============+=========+
| admin-state | Set PW admin-state | | enabled    | enabled |
|             |                    | | disabled   |         |
+-------------+--------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-vpws-inst-pw)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
