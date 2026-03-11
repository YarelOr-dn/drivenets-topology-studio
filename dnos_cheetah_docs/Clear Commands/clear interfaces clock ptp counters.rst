clear interfaces clock ptp counters
-----------------------------------

**Minimum user role:** operator

Clearing the interface PTP port counters resets the counters to zero and removes the counter information from the database.

To clear the interface counters:

**Command syntax: clear interfaces clock ptp counters [interface-name]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. **Parameter table:**

**Example**
::

	dnRouter# clear interfaces clock ptp counters
	dnRouter# clear interfaces clock ptp counters ge400-1/1/1
	dnRouter# clear interfaces clock ptp counters ge400-1/1/1.134


.. **Help line:** clear clock ptp port counters

**Command History**

+-------------+---------------------------------------+
|             |                                       |
| Release     | Modification                          |
+=============+=======================================+
| 18.0        | Command introduced                    |
+-------------+---------------------------------------+
