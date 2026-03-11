clear isis process
------------------

**Minimum user role:** operator

To clear the IS-IS database and reset IS-IS adjacencies:

**Command syntax: clear isis** instance [isis-instance-name] **process**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - use "instance [isis-instance-name]" to clear from a specific ISIS instance


**Parameter table:**

+-----------------------+--------------------------------------------------------------------+---------------------+-------------+
|                       |                                                                    |                     |             |
| Parameter             | Description                                                        | Range               | Default     |
+=======================+====================================================================+=====================+=============+
|                       |                                                                    |                     |             |
| no parameter          | Clear the entire IS-IS database                                    | \-                  | \-          |
+-----------------------+--------------------------------------------------------------------+---------------------+-------------+
|                       |                                                                    |                     | \-          |
| isis-instance-name    | Clear IS-IS neighbor adjacencies for the specified IS-IS instance  | 1..255 characters   |             |
+-----------------------+--------------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# clear isis process
	dnRouter# clear isis process ISIS_A process

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+
