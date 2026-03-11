network-services evpn instance mac-handling loop-prevention
-----------------------------------------------------------

**Minimum user role:** operator

Enter the loop-prevention hierarchy to modify the loop-prevention attributes for this EVPN instance.

**Command syntax: loop-prevention**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To revert the loop-prevention configuration for this instance to the defaults.
::

    dnRouter(ccfg-evpn-inst-mh)# no loop-prevention

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
