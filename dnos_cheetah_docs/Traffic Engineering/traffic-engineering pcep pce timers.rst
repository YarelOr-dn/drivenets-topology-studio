traffic-engineering pcep pce timers
-----------------------------------

**Minimum user role:** operator

There are two sets of PCEP PCE timers:

-	Session maintenance timers - used for message transmission between PCC and PCE to notify one another of their availability. The session maintenance timers are based on keep-alive timers (see "mpls traffic-engineering pcep pce timers keep-alive") and dead timers (see"mpls traffic-engineering pcep pce timers dead-timer").

-	Session disconnection timers - determining what to do when a session unexpectedly disconnects. These timers are for the redelegation of a new PCE (see "mpls traffic-engineering pcep pce timers redelegation-timeout") and for removal of the LSPs from the disconnected PCE (see "mpls traffic-engineering pcep pce timers lsp-state-timeout").

To set timers for messaging between PCC and the specific PCE:


**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# timers
	dnRouter(cfg-pcep-pce-timers)#

**Removing Configuration**

To revert all timers to their default values:
::

	dnRouter(cfg-te-pcep-pce)# no timers


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+