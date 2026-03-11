show interfaces lfs
-------------------

**Minimum user role:** viewer

To display the interfaces' current signaled fault, if any exists, and all signaled local/remote fault statistics:

**Command syntax: show interfaces lfs** [interface-name]

**Command mode:** operational

**Note**

- This command is applicable to physical interfaces.


**Parameter table**

+----------------+--------------------------------------------+---------------------------------+
| Parameter      | Description                                | Range                           |
+================+============================================+=================================+
| interface-name | Filter the display to a specific interface | ge<interface speed>-<A>/<B>/<C> |
+----------------+--------------------------------------------+---------------------------------+

**Example**
::

  dnRouter# show interfaces lfs ge100-0/0/19

  Interface ge100-0/0/19 Signaled Faults
      Current Fault status: Remote Fault
    Total Local Faults detected: 2
    Total Remote Faults detected: 3
    Total number of faults detected: 5

  dnRouter# show interfaces lfs

  | Interface    | Under Fault   |   Local Faults |   Remote Faults |   Total Faults |
  |--------------+---------------+----------------+-----------------+----------------|
  | ge100-0/0/0  | None          |              0 |               0 |              0 |
  | ge100-0/0/1  | None          |              0 |               0 |              0 |
  | ge100-0/0/2  | None          |              0 |               0 |              0 |
  | ge100-0/0/3  | None          |              0 |               0 |              0 |
  | ge100-0/0/4  | None          |              0 |               0 |              0 |
  | ge100-0/0/5  | None          |              0 |               0 |              0 |
  | ge100-0/0/6  | None          |              0 |               0 |              0 |
  | ge100-0/0/7  | None          |              0 |               0 |              0 |
  | ge100-0/0/8  | None          |              0 |               0 |              0 |
  | ge100-0/0/9  | None          |              0 |               0 |              0 |
  | ge100-0/0/19 | Remote Fault  |              2 |               3 |              5 |
  | ge100-0/0/20 | None          |              0 |               0 |              0 |


.. **Help line:** show 100GE and 400GE physical interfaces signaled faults

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
