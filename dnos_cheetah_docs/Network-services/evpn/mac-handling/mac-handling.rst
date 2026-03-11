network-services evpn mac-handling
----------------------------------

**Minimum user role:** operator

Enter the mac-learning hierarchy to modify the default mac-learning attributes for any new EVPN instances that are subsequently created.

**Command syntax: mac-handling**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To revert the mac-handling configurations to defaults
::

    no mac-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
