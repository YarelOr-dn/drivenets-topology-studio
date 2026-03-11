clear vpws counters
-------------------

**Minimum user role:** operator

To reset the VPWS service instance counters:

**Command syntax: clear vpws [instance-name] counters**

**Command mode:** operation

.. **Hierarchies**

**Note**

- The Attachment Circuit (AC) counters are not reset.

**Parameter table**

+---------------+-------------------------------+--------+---------+
| Parameter     | Description                   | Range  | Default |
+===============+===============================+========+=========+
| instance-name | The configured VPWS instance. | String | \-      |
|               |                               | 1..255 |         |
+---------------+-------------------------------+--------+---------+

**Example**
::

	dnRouter# clear vpws R15_R16_1 counters


.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 16.1    | Command introduced                                |
+---------+---------------------------------------------------+
