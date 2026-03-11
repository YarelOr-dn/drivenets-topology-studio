traffic-engineering pcep timers keep-alive
------------------------------------------

**Minimum user role:** operator

PCEP keep-alive messages are used to maintain PCEP sessions. Once a session is established, the PCE or PCC is periodically informed whether or not its PCEP peer is still available for use. 

Each end of a PCEP session runs a keep-alive timer. When the timer expires, it sends a keep-alive message to its peer and restarts the timer. The Keep-alive timer value is negotiated between the PCC and PCE during PCEP session establishment. If the two timers are not identical, then the timer that will be selected for the session is the minimum between the configured keep-alive timer and the keep-alive received from the PCE in the OPEN message.

To configure the interval between keep-alive messages between PCC and PCE:


**Command syntax: keep-alive [interval]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep timers

**Note**

- The session can only be established if the received PCE keep-alive < the received PCE dead-timer.

**Parameter table**

+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                                                                            |           |             |
| Parameter     | Description                                                                                                                                                                                | Range     | Default     |
+===============+============================================================================================================================================================================================+===========+=============+
|               |                                                                                                                                                                                            |           |             |
| interval      | The time (in seconds) that the PCE or PCC waits   after sending a keep-alive message to its PCEP peer, before sending another   keep-alive message notifying the peer of its availability. | 0..255    | 10          |
|               |                                                                                                                                                                                            |           |             |
|               | A value of 0 means that keep-alive messages will   not be sent.                                                                                                                            |           |             |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# timers
	dnRouter(cfg-te-pcep-timers)# keep-alive 30

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-te-pcep-timers)# no keep-alive


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+