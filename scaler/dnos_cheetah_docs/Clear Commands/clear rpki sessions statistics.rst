clear rpki sessions statistics
------------------------------

**Minimum user role:** operator

To clear rpki sessions statistics:

**Command syntax: clear rpki sessions** [server-address] **statistics**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+----------------+-------------------------------------------+-------------------------+---------+
| Parameter      | Description                               | Range                   | Default |
+================+===========================================+=========================+=========+
| server-address | Clear the statistics of a specific server | IP-address or hostname  | \-      |
+----------------+-------------------------------------------+-------------------------+---------+


**Example**
::

	dnRouter# clear rpki sessions statistics
	dnRouter# clear rpki sessions 1.1.1.1 statistics
	dnRouter# clear rpki sessions 2001:125:125::1 statistics
	dnRouter# clear rpki sessions rpkiv.drivenets.com statistics


.. **Help line:**

**Command History**

+----------+-----------------------------------------------------+
| Release  | Modification                                        |
+==========+=====================================================+
| 15.1     | Command introduced                                  |
+----------+-----------------------------------------------------+
| 16.2     | Replaced server-id parameter with server-address    |
+----------+-----------------------------------------------------+
