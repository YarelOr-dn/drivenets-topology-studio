network-services evpn mac-handling loop-prevention loop-detection-threshold
---------------------------------------------------------------------------

**Minimum user role:** operator

Configure the number of moves allowed within the loop-detection-window period, the default is 5. If the loop-detection-threshold is reached within this period the mac address is suppressed.

**Command syntax: loop-detection-threshold [loop-detection-threshold]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling loop-prevention

**Parameter table**

+--------------------------+----------------------------------+-------+---------+
| Parameter                | Description                      | Range | Default |
+==========================+==================================+=======+=========+
| loop-detection-threshold | the number of mac moves allowed. | 2-100 | 5       |
+--------------------------+----------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# loop-prevention
    dnRouter(cfg-evpn-mh-lp)# loop-detection-threshold 6
    dnRouter(cfg-evpn-mh-lp)#


**Removing Configuration**

To restore the loop-detection-window period to its default value of 5.
::

    dnRouter(cfg-evpn-mh-lp)# no loop-detection-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
