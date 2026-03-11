protocols segment-routing pcep timers keep-alive
------------------------------------------------

**Minimum user role:** operator

PCEP keep-alive messages are used to maintain PCEP sessions. Once a session is established, the PCE or PCC is periodically informed whether or not its PCEP peer is still available for use.

Each end of a PCEP session runs a keep-alive timer.
When the timer expires, it sends a keep-alive message to its peer and restarts the timer.
The Keep-alive timer value is negotiated between the PCC and PCE during PCEP session establishment.
If the two timers are not identical, then the timer that will be selected for the session is the minimum between the configured keep-alive timer and the keep-alive received from the PCE in the OPEN message.

To configure the interval between keep-alive messages between PCC and PCE:

**Command syntax: keep-alive [keep-alive]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep timers

**Parameter table**

+------------+----------------------------------------------------------+-------+---------+
| Parameter  | Description                                              | Range | Default |
+============+==========================================================+=======+=========+
| keep-alive | time interval to keep-alive messages between PCC and PCE | 0-255 | 10      |
+------------+----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# timers
    dnRouter(cfg-sr-pcep-timers)# keep-alive 10


**Removing Configuration**

To revert keep-alive configuration to default:
::

    dnRouter(cfg-sr-pcep-timers)# no keep-alive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
