traffic-engineering pcep timers dead-timer
------------------------------------------

**Minimum user role:** operator

The dead-timer is another PCEP session maintenance timer that works in tandem with the keep-alive timer (see "mpls traffic-engineering pcep timers keep-alive"). Both PCE and PCC run dead timers and restart them whenever a message is received on the session. If one session end does not receive a message before the dead timer expires, it declares the session dead.

The dead timer value is negotiated between the PCC and PCE during PCEP session establishment. If the two timers are not identical, then the timer that will be selected for the session is the maximum between the configured dead-timer and the dead-timer received from the PCE in the OPEN message.

To configure the dead-timer's timeout interval:


**Command syntax: dead-timer [interval]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep timers

**Parameter table**

+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                                                                      |           |             |
| Parameter     | Description                                                                                                                                                                          | Range     | Default     |
+===============+======================================================================================================================================================================================+===========+=============+
|               |                                                                                                                                                                                      |           |             |
| interval      | The time (in seconds) that the PCE or PCC waits   after receiving a keep-alive message from its PCEP peer, before declaring the   peer dead.                                         | 0..255    | 40          |
|               |                                                                                                                                                                                      |           |             |
|               | For the session to be established, the value of   the dead-timer interval must be higher than the PCE keep-alive timer (see "mpls   traffic-engineering pcep pce timers keep-alive") |           |             |
|               |                                                                                                                                                                                      |           |             |
|               | A value of 0 means that the session will not be   timed out, even if keep-alive messages are no longer received on the session.                                                      |           |             |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# timers
	dnRouter(cfg-te-pcep-timers)# dead-timer 50

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-te-pcep-timers)# no dead-timer


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+