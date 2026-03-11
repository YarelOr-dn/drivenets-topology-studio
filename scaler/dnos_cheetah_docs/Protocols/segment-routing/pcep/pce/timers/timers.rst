protocols segment-routing pcep pce priority address timers
----------------------------------------------------------

**Minimum user role:** operator

There are two sets of PCEP timers:
-  Session maintenance timers - used for message transmission between PCC and PCE to notify one another of their availability. The session maintenance timers are based on keep-alive timers (see "pcep timers keep-alive") and dead timers (see "pcep timers dead-timer").
-  Session disconnection timers - determining what to do when a session unexpectedly disconnects. These timers are for the redelegation of a new PCE (see "pcep timers redelegation-timeout") and for removal of the LSPs from the disconnected PCE (see "pcep timers lsp-state-timeout").

To set global timers for messaging between PCC and PCE:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#  pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# timers
    dnRouter(cfg-pcep-pce-timers)#


**Removing Configuration**

To revert all sr-te pcep timers configuration to default:
::

    dnRouter(cfg-sr-pcep-pce)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
