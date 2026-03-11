protocols segment-routing pcep timers
-------------------------------------

**Minimum user role:** operator

There are two sets of PCEP timers:
-  Session maintenance timers - used for message transmission between PCC and PCE to notify one another of their availability. The session maintenance timers are based on keep-alive timers (see "pcep timers keep-alive") and dead timers (see "pcep timers dead-timer").
-  Session disconnection timers - determining what to do when a session unexpectedly disconnects. These timers are for the redelegation of a new PCE (see "pcep timers redelegation-timeout") and for removal of the LSPs from the disconnected PCE (see "pcep timers lsp-state-timeout").

To set global timers for messaging between PCC and PCE:

To configure pcep, enter pcep configuration mode:

**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# timers
    dnRouter(cfg-sr-pcep-timers)#


**Removing Configuration**

To revert all sr-te pcep timers configuration to default:
::

    dnRouter(cfg-protocols-sr-pcep)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
