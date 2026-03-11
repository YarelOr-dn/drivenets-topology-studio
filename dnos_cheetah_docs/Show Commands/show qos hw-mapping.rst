show qos hw-mapping
-------------------

**Minimum user role:** viewer

To display qos hw-mapping:

**Command syntax: show qos hw-mapping**

**Command mode:** operational

**Example**
::

  dnRouter# show qos hw-mapping

  Area: Queue sizes and thresholds, Mapping: Temporal unit conversion, Method: Speed ranges
  Admin state: enabled

  +---------------+---------------+---------------+
  | from          | upto          | use           |
  +---------------+---------------+---------------+
  | 0             | 100 mbps      | 100 mbps      |
  +---------------+---------------+---------------+
  | 100 mbps      | 1 gbps        | 1 gbps        |
  +---------------+---------------+---------------+
  | 1 gbps        | 40 gbps       | 10 gbps       |
  +---------------+---------------+---------------+
  | 40 gbps       | 200 gbps      | 100 gbps      |
  +---------------+---------------+---------------+
  | 200 gbps      | 4000 gbps     | 400 gbps      |
  +---------------+---------------+---------------+


**Note:**

 - Table should be in ascending order

 - From is implicit to the previous upto. First row starts with 0.

 - Unit conversion (kbps, mbps, gbps) should be according to the smallest possible unit, without loss of accuracy.

.. **Help line:** show qos global policy maps

**Parameter table:**

+-------------+---------------------+-------------------------------------------------------+
| Parameter   | Values              |                                                       |
+=============+=====================+=======================================================+
| from        | 0..1000000000 kbps  | speed range start (exclusive)                         |
+-------------+---------------------+-------------------------------------------------------+
| upto        | 0..1000000000 kbps  | speed range end (inclusive)                           |
+-------------+---------------------+-------------------------------------------------------+
| use         | 0..1000000000 kbps  | speed selected for temporal unit conversion           |
+-------------+---------------------+-------------------------------------------------------+

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
