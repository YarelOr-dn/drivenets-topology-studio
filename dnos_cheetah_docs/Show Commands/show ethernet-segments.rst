show ethernet-segments
----------------------

**Minimum user role:** operator

To show information relating to the ethernet-segments that have been defined.

**Command syntax: show ethernet-segments** 

**Command mode:** operational



**Example**
::

  dnRouter# show ethernet-segments

  Number of ethernet segments: 1

  | ESI                             | Mode             | Interface         | State             | ACs   |
  +---------------------------------+------------------+-------------------+-------------------+-------+
  | 00:12:01:11:94:00:00:00:00:01   | single-active    | ge400-0/0/10      | up                | 3     |

  

.. **Help line:** show detailed information for EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+