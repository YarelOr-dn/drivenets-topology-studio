protocols isis instance interface bfd min-rx
--------------------------------------------

**Minimum user role:** operator

The desired minimum receive interval is the time-frame in which a BFD packet is expected to arrive. If a BFD packet is not received within the configured interval, the BFD session will go down.
The min-rx together with the multiplier, defines the detection time.
The Local Detection timeout = negotiated Rx interval * remote_multiplier (the multiplier value received on the BFD packet).
The Remote Detection timeout = negotiated Tx interval * local_multiplier (the multiplier value configured locally for the session).
Set the desired minimum receive interval for the BFD session:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Note**

- Due to hardware limitation, maximum supported transmit rate is 1700 msec, and negotiated transmit interval higher than 1700 msec will result in actual transmit rate of 1700 msec.

**Parameter table**

+-----------+---------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                         | Range  | Default |
+===========+=====================================================================+========+=========+
| min-rx    | The interval (in msec) in which a BFD packet is expected to arrive. | 5-1700 | 300     |
+-----------+---------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# min-rx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-if-bfd)# no min-rx

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 12.0    | Command introduced                |
+---------+-----------------------------------+
| 15.1    | Added support for 5 msec interval |
+---------+-----------------------------------+
