network-services vpws instance pw ignore-mtu-mismatch
-----------------------------------------------------

**Minimum user role:** operator

To establish the Pseudowire even if the local Pseudowire signaled MTU differs from the remote MTU:

**Command syntax: ignore-mtu-mismatch [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Support PW establishment even when PW local signaled mtu differs from PW remote  | | enabled    | disabled |
|             | signaled mtu                                                                     | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# ignore-mtu-mismatch enabled


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-vpws-inst-pw)# no ignore-mtu-mismatch

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
