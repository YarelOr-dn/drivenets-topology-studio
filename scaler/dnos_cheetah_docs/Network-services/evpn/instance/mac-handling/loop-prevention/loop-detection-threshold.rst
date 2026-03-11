network-services evpn instance mac-handling loop-prevention loop-detection-threshold
------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the number of moves allowed within the loop-detection-window period. If the loop-detection-threshold is reached within this period the mac address will be suppressed. Default is defined at the EVPN level.

**Command syntax: loop-detection-threshold [loop-detection-threshold]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance mac-handling loop-prevention

**Parameter table**

+--------------------------+----------------------------------+-------+---------+
| Parameter                | Description                      | Range | Default |
+==========================+==================================+=======+=========+
| loop-detection-threshold | the number of mac moves allowed. | 2-100 | \-      |
+--------------------------+----------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# mac-handling
    dnRouter(cfg-evpn-inst-mh)# loop-prevention
    dnRouter(cfg-inst-mh-lp)# loop-detection-threshold 6
    dnRouter(cfg-inst-mh-lp)#


**Removing Configuration**

To restore the loop-detection-window period to its default value.
::

    dnRouter(cfg-inst-mh-lp)# no loop-detection-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
