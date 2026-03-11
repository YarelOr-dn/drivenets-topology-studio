protocols msdp peer-timers hold-time
------------------------------------

**Minimum user role:** operator

You can use this command to set the MSDP peering connectivity hold-time timer. The command can also be invoked under the MSDP default-peer and MSDP mesh-group peer hierarchies. The hold-time timer is set to time-out the connection in the event that no TLV is received from the related peer. The timer is defined per MSDP peer connection. Every MSDP TLV received from the related MSDP peer resets the hold-time. Once a timer expires, the MSDP connection on the router is timed-out and the MSDP TCP connection is torn down.

**Command syntax: hold-time [hold-time-timer]**

**Command mode:** config

**Hierarchies**

- protocols msdp peer-timers

**Note**
- The hold-time timer must be greater than the keep-alive timer. The user is warned in case the keep-alive timer is greater or equal to hold-time.

**Parameter table**

+-----------------+-----------------+--------+---------+
| Parameter       | Description     | Range  | Default |
+=================+=================+========+=========+
| hold-time-timer | hold-time-timer | 20-180 | 80      |
+-----------------+-----------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# peer-timers
    dnRouter(cfg-protocols-msdp-peer-timers)# hold-time 90

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# peer-timers
    dnRouter(cfg-protocols-msdp-default-peer-peer-timers)# hold-time 90

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-mesh-group)# peer 2.2.2.2
    dnRouter(cfg-protocols-msdp-mesh-group-peer)# peer-timers
    dnRouter(cfg-protocols-msdp-mesh-group-peer-peer-timers)# hold-time 90


**Removing Configuration**

To return the hold-time setting to its default value:
::

    dnRouter(cfg-protocols-msdp-peer-timers)# no hold-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
