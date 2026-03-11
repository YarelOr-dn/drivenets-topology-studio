protocols segment-routing pcep pce priority address timers dead-timer
---------------------------------------------------------------------

**Minimum user role:** operator

The dead-timer is another PCEP session maintenance timer that works in tandem with the keep-alive timer (see "segment-routing pcep pce timers keep-alive"). Both PCE and PCC run dead timers and restart them whenever a message is received on the session. If one session end does not receive a message before the dead timer expires, it declares the session dead.

The dead timer value is negotiated between the PCC and PCE during PCEP session establishment. If the two timers are not identical, then the timer that will be selected for the session is the maximum between the configured dead-timer and the dead-timer received from the PCE in the OPEN message.

To configure the dead-timer's timeout interval:

**Command syntax: dead-timer [dead-timer]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address timers

**Parameter table**

+------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                                      | Range | Default |
+============+==================================================================================+=======+=========+
| dead-timer | timeout interval for PCC and PCE session if the PCC does not receive keep-alive  | 0-255 | \-      |
|            | messages from the PCE                                                            |       |         |
+------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#  pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# timers
    dnRouter(cfg-pcep-pce-timers)# dead-timer 50


**Removing Configuration**

To revert dead-timer configuration to default:
::

    dnRouter(cfg-pcep-pce-timers)# no dead-timer

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
