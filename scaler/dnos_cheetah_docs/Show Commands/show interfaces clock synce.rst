show interfaces clock synce
---------------------------

**Minimum user role:** viewer

To display the interfaces' timing configuration and statistics:

**Command syntax: show interfaces clock synce** [interface-name]

**Command mode:** operational

**Note**

- Command applicable to ethernet interfaces.
- Command applicable to physical and breakout interfaces.

**Parameter table**

+----------------+--------------------------------------------+----------------------------------+
| Parameter      | Description                                | Range                            |
+================+============================================+==================================+
| interface-name | Filter the display to a specific interface | ge<interface speed>-<A>/<B>/<C>  |
|                |                                            |    <A> - ncp id                  |
|                |                                            |    <B> - slot id                 |
|                |                                            |    <C> - port id                 |
+----------------+--------------------------------------------+----------------------------------+

**Example**
::

  dnRouter# show interfaces clock synce ge400-0/0/19

  Interface ge400-0/0/19 clock mode and statistics
    Mode:              synchronous
    Received packets:  1
    Sent packets:      2
    Received w. DNU:   4
    Sent w. DNU:       5

**Example**
::

  dnRouter# show interfaces clock synce

  | Interface    | Mode     |  Received     | Sent        | Received     | Sent         |
  |              |          |  packets      | with DNU    | with DNU     |              |
  |--------------+----------+---------------+-------------+--------------+--------------|
  | ge400-0/0/0  | sync     | 123           | 4324        | 5            | 3            |
  | ge400-0/0/1  | non-sync | 123           | 324         | 0            | 0            |
    ...

.. **Help line:** Display synchronous-ethernet timing configuration and statistics of physical and breakout interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
