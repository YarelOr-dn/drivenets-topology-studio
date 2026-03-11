clear isis statistics
---------------------

**Minimum user role:** operator

To clear IS-IS statistics:

**Command syntax: clear isis** instance [isis-instance-name] **statistics**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - use "instance [isis-instance-name]" to clear from a specific ISIS instance


**Parameter table:**

+-----------------------+-------------------------------------------------------------+---------------------+-------------+
|                       |                                                             |                     |             |
| Parameter             | Description                                                 | Range               | Default     |
+=======================+=============================================================+=====================+=============+
|                       |                                                             |                     |             |
| no parameter          | Clear all IS-IS statistics                                  | \-                  | \-          |
+-----------------------+-------------------------------------------------------------+---------------------+-------------+
|                       |                                                             |                     | \-          |
| isis-instance-name    | Clear IS-IS statistics from the specified IS-IS instance    | 1..255 characters   |             |
+-----------------------+-------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# clear isis statistics
	dnRouter# clear isis instance ISIS_A statistics


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+