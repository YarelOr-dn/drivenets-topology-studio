show interfaces clock ptp fmt
-----------------------------

**Minimum user role:** viewer

To display the interfaces' PTP Foreign-Master-Table dataset:

**Command syntax: show interfaces clock ptp fmt** [interface-name]

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

  dnRouter# show interfaces clock ptp fmt ge400-0/0/19

  Interface ge400-0/0/19 clock Foreign-Master-Table dataset:
    State:               Slave
    Best foreign-master: 04:05:AA:FE:EF:08:9A:00

  | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
  |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
  |-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
  | 04:05:AA:FE:EF:08:9A:00 | False     | BA:4E:1F:28:3A:10 | D4:05:AA:FE:EF:08:9A:01 | PTP                 | 6      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |
  | 14:15:00:FD:CF:18:2B:E0 | False     | AA:AE:AF:A8:AA:A0 | D5:06:A7:F8:E9:01:9B:02 | internal-oscillator | 7      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |
   ...

**Example**
::

  dnRouter# show interfaces clock ptp fmt ge400-0/0/11

  Interface ge400-0/0/19 clock Foreign-Master-Table dataset:
    State:               Disabled

**Example**
::

  dnRouter# show interfaces clock ptp fmt

  Interface ge400-0/0/0 clock Foreign-Master-Table dataset;
    State:               Slave
    Best foreign-master: 05:06:A7:F8:E9:0A:9B:0C

  | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
  |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
  |-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
  | 05:06:A7:F8:E9:0A:9B:0C | False     | 0A:0E:0F:02:0A:11 | D4:05:AA:FE:EF:08:9A:01 | atomic-clock        | 140    | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |


  Interface ge400-0/0/19 clock Foreign-Master-Table dataset:
    State:               Slave
    Best foreign-master: 14:15:00:FD:CF:18:2B:E0

  | FM identity             | Alternate | FM L2 Address     | GM Identity             | Time                | GM clk | GM clk   | GM clk | GM     | Steps   | UTC          | UTC offset | Leap  | Leap  | Time   | Freq.  |
  |                         | master    |                   |                         | source              | class  | accuracy | offset | prio.2 | removed | offset (sec) | valid      | 59    | 61    | Trace. | Trace. |
  |-------------------------+-----------+-------------------+-------------------------+---------------------+--------+----------+--------+--------+---------+--------------+------------+-------+-------+--------+--------|
  | 04:05:AA:FE:EF:08:9A:00 | False     | BA:4E:1F:28:3A:10 | D4:05:AA:FE:EF:08:9A:01 | PTP                 | 6      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |
  | 14:15:00:FD:CF:18:2B:E0 | False     | AA:AE:AF:A8:AA:A0 | D5:06:A7:F8:E9:01:9B:02 | internal-oscillator | 7      | 0xFE     | 0xFFFF | 128    | 12      | 2            | True       | False | False | False  | False  |

    ...

**Example**
::

    dnRouter# show system clock ptp

        Requested data is unavailable.

.. **Help line:** Display PTP port Foreign-Master-Table dataset of physical and breakout interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
