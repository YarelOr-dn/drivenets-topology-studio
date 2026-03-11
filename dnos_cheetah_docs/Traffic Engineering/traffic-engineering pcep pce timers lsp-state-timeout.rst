traffic-engineering pcep pce timers lsp-state-timeout
-----------------------------------------------------

**Minimum user role:** operator

When a PCEP session with a PCE disconnects, the PCC redelegates to an alternative PCE. The LSP-state-timeout is the amount of time after redelegation that the PCC waits before flushing the LSP states associated with the disconnected PCEP session and reverting to the local default configurations. This operation is performed in a make-before-break fashion.

To configure the lsp-state-timeout:


**Command syntax: lsp-state-timeout {[interval] \| infinity}**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce timers

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------+----------------------------------+
|               |                                                                                                                                                                      |            |                                  |
| Parameter     | Description                                                                                                                                                          | Range      | Default                          |
+===============+======================================================================================================================================================================+============+==================================+
|               |                                                                                                                                                                      |            |                                  |
| interval      | The time (in seconds) that the PCC waits before   removing the LSPs associated with a disconnected PCEP session and reverting   to the local default configurations. | 0..3600    | The TE PCEP lsp-state-timeout    |
|               |                                                                                                                                                                      |            |                                  |
|               | The timer starts when the session with the   primary PCE is closed. When a new PCE is redelegated, the timer resets.                                                 |            |                                  |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------+----------------------------------+
|               |                                                                                                                                                                      |            |                                  |
| infinity      | The parameter configuration set by the PCE will   remain intact until the PCC specifically takes action to change them.                                              | \-         | \-                               |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------+----------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 1 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# timers
	dnRouter(cfg-pcep-pce-timers)# lsp-state-timeout 20
	
	
	dnRouter(cfg-mpls-te-pcep)# pce priority 2 address 2.2.2.2
	dnRouter(cfg-te-pcep-pce)# timers
	dnRouter(cfg-pcep-pce-timers)# lsp-state-timeout infinity

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-te-pcep-pce)# no lsp-state-timeout


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+