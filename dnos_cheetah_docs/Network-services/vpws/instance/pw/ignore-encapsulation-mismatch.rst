network-services vpws instance pw ignore-encapsulation-mismatch
---------------------------------------------------------------

**Minimum user role:** operator

To establish the Pseudowire even if the local Pseudowire encapsulation type differs from the remote Pseudowire encapsulation type:

**Command syntax: ignore-encapsulation-mismatch [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Parameter table**

+-------------+------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                  | Range        | Default  |
+=============+==============================================================================+==============+==========+
| admin-state | Support PW establishment even when PW local type differs from PW remote type | | enabled    | disabled |
|             |                                                                              | | disabled   |          |
+-------------+------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# ignore-encapsulation-mismatch enabled


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-vpws-inst-pw)# no ignore-encapsulation-mismatch

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
