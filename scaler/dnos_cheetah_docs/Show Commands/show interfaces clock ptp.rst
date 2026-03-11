show interfaces clock ptp
-------------------------

**Minimum user role:** viewer

To display the interfaces' PTP port configuration and state parameters:

**Command syntax: show interfaces clock ptp** [interface-name]

**Command mode:** operational

**Note**

- Command applicable to ethernet interfaces.
- Command applicable to physical and breakout interfaces.
- When the PTP feature is disabled or node is not in an operational state, data will not be available.

**Parameter table**

+----------------+--------------------------------------------+---------------------------------+
| Parameter      | Description                                | Range                           |
+================+============================================+=================================+
| interface-name | Filter the display to a specific interface | ge<interface speed>-<A>/<B>/<C> |
|                |                                            |    X   - port speed             |
|                |                                            |    <f> - ncp id                 |
|                |                                            |    <n> - slot id                |
|                |                                            |    <p> - port id                |
+----------------+--------------------------------------------+---------------------------------+

**Example**
::

  dnRouter# show interfaces clock ptp ge400-0/0/19

  Interface ge400-0/0/19 PTP port parameters:
    Mode:                         enabled
    Port number:                  13
    State:                        Master
    Profile:                      G.8275.1
    State last change time:       27-Jun-2023 08:07:03 UTC
    Master-only:                  False
    Local priority:               128
    Announce-receipt-timeout:     3
    Multicast address:            non-forwardable
    Delay:                        0 nsec
    Log-announce-interval:        -3
    Log-min-delay-req-interval:   -4
    Log-sync-interval:            -4
    Transport:                    802.3

**Example**
::

  dnRouter# show interfaces clock ptp

  | Interface    | Mode     | Port   | Profile    | State  | State last change        | Master | Local    | Multicast       | Delay   |
  |              |          | Number |            |        |                          | only   | priority | Address         | [nsec]  |
  |--------------+----------+--------+------------+--------+--------------------------+--------+----------+-----------------+---------|
  | ge400-0/0/0  | enabled  | 1      | G.8275.1   | Master | 27-Jun-2023 08:07:03 UTC | False  | 128      | Non-forwardable | 0       |
  | ge400-0/0/1  | disabled | 12     | G.8275.1   | Slave  | 27-Jun-2023 08:06:03 UTC | False  | 128      | Forwardable     | -100000 |

**Example**
::

  dnRouter# show interfaces clock ptp

  | Interface    | Mode     | Port   | Profile    | State  | State last change        | Master | Local    | Multicast       | Delay   |
  |              |          | Number |            |        |                          | only   | priority | Address         | [nsec]  |
  |--------------+----------+--------+------------+--------+--------------------------+--------+----------+-----------------+---------|
  | ge400-0/0/0  | enabled  | 1      | G.8275.1   | Master | 27-Jun-2023 04:07:03 UTC | False  | 128      | Non-forwardable | 0       |
  | ge400-0/0/1  | disabled | 12     | G.8275.1   | Slave  | 27-Jun-2023 05:07:03 UTC | False  | 128      | Forwardable     | -100000 |
    ...

**Example**
::

    dnRouter# show interfaces clock ptp

        Requested data is unavailable.

.. **Help line:** Display PTP port configuration and state parameters of physical and breakout interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
