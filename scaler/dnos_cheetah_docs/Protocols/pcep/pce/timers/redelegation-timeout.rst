protocols segment-routing pcep pce priority address timers redelegation-timeout
-------------------------------------------------------------------------------

**Minimum user role:** operator

The redelegation-timeout interval is the amount of time that a PCC waits before revoking LSP delegations to a PCE with which the PCEP session has terminated unexpectedly and attempting to redelegate the LSPs to an alternate PCE. If the PCEP session with the original PCE is restored before the redelegation timer expires, the LSP delegations will not be revoked.

To configure the redelegation-timeout interval:

**Command syntax: redelegation-timeout [timeout]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address timers

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                                      | Range  | Default |
+===========+==================================================================================+========+=========+
| timeout   | time (in seconds) that a path computation client (PCC) must wait before          | 0-3600 | \-      |
|           | re-delegating LSPs after a PCEP session with the active stateful PCE is          |        |         |
|           | disconnected                                                                     |        |         |
+-----------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#  pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# timers
    dnRouter(cfg-pcep-pce-timers)# redelegation-timeout 2000


**Removing Configuration**

To revert redelegation-timeout configuration to default:
::

    dnRouter(cfg-pcep-pce-timers)# no redelegation-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
