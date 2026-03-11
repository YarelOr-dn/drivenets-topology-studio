protocols msdp default-peer peer-timers keep-alive
--------------------------------------------------

**Minimum user role:** operator

You can use this command to set the MSDP peering connectivity keep-alive timer. The command can also be invoked under the MSDP default-peer and MSDP mesh-group peer hierarchies. The keep-alive timer is set to time-out the connection in the event that a keepalive TLV is sent to a certain MSDP peer. In that event, the MSDP daemon sets a keep alive timer for that connection and the expiration of the timer should trigger an additional keepalive TLV (unless a different TLV is sent to the specific MSDP peer, which in turn will reset the keepalive timer for that specific MSDP peer connection).

**Command syntax: keep-alive [keep-alive-timer]**

**Command mode:** config

**Hierarchies**

- protocols msdp default-peer peer-timers

**Note**
- This command may be also be invoked inside mesh-group peer or inside default-peer configuration hierarchy.

- The hold-time timer must be greater than the keep-alive timer. The user is warned in case the keep-alive timer is greater or equal to hold-time.

**Parameter table**

+------------------+------------------+-------+---------+
| Parameter        | Description      | Range | Default |
+==================+==================+=======+=========+
| keep-alive-timer | keep-alive-timer | 10-60 | \-      |
+------------------+------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# peer-timers
    dnRouter(cfg-protocols-msdp-peer-timers)# keep-alive 30
    dnRouter(cfg-protocols-msdp-peer-timers)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 12.1.40.111
    dnRouter(cfg-protocols-msdp-default-peer)# peer-timers
    dnRouter(cfg-protocols-msdp-default-peer-peer-timers)# keep-alive 30

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# mesh-group MSDP_Domain_X
    dnRouter(cfg-protocols-msdp-mesh-group)# peer 2.2.2.2
    dnRouter(cfg-protocols-msdp-mesh-group-peer)# peer-timers
    dnRouter(cfg-protocols-msdp-mesh-group-peer-peer-timers)# keep-alive 30


**Removing Configuration**

To return the keep-alive setting to its default value:
::

    dnRouter(cfg-protocols-msdp-peer-timers)# no keep-alive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
