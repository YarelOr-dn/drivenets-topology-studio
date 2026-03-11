show interfaces clock ptp stats
-------------------------------

**Minimum user role:** viewer

To display the interfaces' PTP state and statistics:

**Command syntax: show interfaces clock ptp stats** [interface-name]

**Command mode:** operational

**Note**

- Command applicable to ethernet interfaces.
- Command applicable to physical and breakout interfaces.
- Command shows PTP statistics only for PTP enabled interfaces.
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

  dnRouter# show interfaces clock ptp stats ge400-0/0/19

  Interface ge400-0/0/19 PTP state and statistics
    State:                        Master
    Received packets:             128
    Sent packets:                 256
    Discarded packets:            3
    Received packets rate (pps):  48
    Sent packets rate (pps):      48

**Example**
::

  dnRouter# show interfaces clock ptp stats

  | Interface    | State    | Received     | Sent        | Discarded    | Received     | Sent         |
  |              |          | packets      | packets     | packets      | rate (pps)   | rate (pps)   |
  |--------------+----------+--------------+-------------+--------------+--------------+--------------|
  | ge400-0/0/0  | Master   | 123          | 4324        | 10           | 5            | 3            |
  | ge400-0/0/1  | Slave    | 123          | 324         | 11           | 0            | 0            |
    ...

**Example**
::

    dnRouter# show interfaces clock ptp stats ge400-0/0/19

        Requested data is unavailable.

**Example**
::

    dnRouter# show interfaces clock ptp stats

        Requested data is unavailable.

.. **Help line:** Display PTP port state and statistics of physical and breakout interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
