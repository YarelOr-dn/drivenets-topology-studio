protocols segment-routing pcep pce priority address timers lsp-state-timeout
----------------------------------------------------------------------------

**Minimum user role:** operator

When a PCEP session with a PCE disconnects, the PCC redelegates to an alternative PCE.
The LSP-state-timeout is the amount of time after redelegation that the PCC waits before flushing the LSP states associated with the disconnected PCEP session and reverting to the local default configurations.
This operation is performed in a make-before-break fashion.

To configure the lsp-state-timeout:

**Command syntax: lsp-state-timeout [timeout]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address timers

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| timeout   | time (in seconds) that a path computation client (PCC) must wait before removing | \-    | \-      |
|           | the LSPs associated with a PCEP session that is disconnected and reverting back  |       |         |
|           | to the local defaults attribtes/configuration                                    |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#  pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# timers
    dnRouter(cfg-pcep-pce-timers)# lsp-state-timeout 20


**Removing Configuration**

To revert lsp-state-timeout configuration to default:
::

    dnRouter(cfg-pcep-pce-timers)# no lsp-state-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
