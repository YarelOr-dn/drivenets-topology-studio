clear interfaces clock esmc counters
------------------------------------

**Minimum user role:** operator

Clearing the interface SyncE ESMC counters resets the counters to zero and removes the counter information from the database.

To clear the interface counters:

**Command syntax: clear interfaces clock esmc counters [interface-name]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. **Parameter table:**

**Example**
::

	dnRouter# clear interfaces clock esmc counters
	dnRouter# clear interfaces clock esmc counters ge400-1/1/1
	dnRouter# clear interfaces clock esmc counters ge400-1/1/1.134


.. **Help line:** clear clock esmc counters

**Command History**

+-------------+---------------------------------------+
|             |                                       |
| Release     | Modification                          |
+=============+=======================================+
| 17.2        | Command introduced                    |
+-------------+---------------------------------------+
