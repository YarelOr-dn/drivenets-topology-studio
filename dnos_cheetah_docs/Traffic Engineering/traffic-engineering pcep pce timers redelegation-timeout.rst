traffic-engineering pcep pce timers redelegation-timeout
--------------------------------------------------------

**Minimum user role:** operator

The redelegation-timeout interval is the amount of time that a PCC waits before revoking LSP delegations to a PCE with which the PCEP session has terminated unexpectedly and attempting to redelegate the LSPs to an alternate PCE. If the PCEP session with the original PCE is restored before the redelegation timer expires, the LSP delegations will not be revoked.

To configure the redelegation-timeout interval:


**Command syntax: redelegation-timeout [interval]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce timers

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------+------------+-------------------------------------+
|               |                                                                                                                                              |            |                                     |
| Parameter     | Description                                                                                                                                  | Range      | Default                             |
+===============+==============================================================================================================================================+============+=====================================+
|               |                                                                                                                                              |            |                                     |
| interval      | The time (in seconds) that the PCC waits after a   PCEP session with the active stateful PCE is disconnected, before   redelegating LSPs.    | 0..3600    | The TE PCEP redelegation-timeout    |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------+------------+-------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# timers
	dnRouter(cfg-pcep-pce-timers)# redelegation-timeout 2000

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-te-pcep-pce)# no redelegation-timeout


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+