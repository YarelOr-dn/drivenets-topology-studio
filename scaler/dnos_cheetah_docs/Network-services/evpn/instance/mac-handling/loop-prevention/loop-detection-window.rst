network-services evpn instance mac-handling loop-prevention loop-detection-window
---------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the period of the loop-detection-window in seconds for this EVPN instance. The default is defined at the EVPN level. If the loop-detection-threshold is reached within this period the mac address is suppressed.

**Command syntax: loop-detection-window [loop-detection-window]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+-----------------------+----------------------------+---------+---------+
| Parameter             | Description                | Range   | Default |
+=======================+============================+=========+=========+
| loop-detection-window | the loop detection period. | 1-10000 | \-      |
+-----------------------+----------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# loop-detection-window 300
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To restore the loop-detection-window period to its default value.
::

    dnRouter(cfg-inst-mh-lp)# no loop-detection-window

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
