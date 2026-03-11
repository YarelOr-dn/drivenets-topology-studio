network-services evpn mac-handling loop-prevention
--------------------------------------------------

**Minimum user role:** operator

Enter the loop-prevention hierarchy to modify the default loop-prevention attributes for the EVPN instances.

**Command syntax: loop-prevention**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To revert the loop-prevention configurations to defaults
::

    dnRouter(cfg-netsrv-evpn-mh)# no loop-prevention

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
