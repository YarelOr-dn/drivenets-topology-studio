clear interfaces counters
-------------------------

**Minimum user role:** operator

Clearing the interface counters resets the counters to zero and removes the counter information from the database. It does not clear SNMP-based and SyncE ESMC counters.

To clear the interface counters:

**Command syntax: clear interfaces counters [interface-name]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces dampening** - clears all counters for **ALL** interfaces

.. - **Clear interfaces dampening interface x** - clears **ALL** counters for a specific interface.

.. **Parameter table:**

**Example**
::

	dnRouter# clear interfaces counters
	dnRouter# clear interfaces counters ge100-1/1/1
	dnRouter# clear interfaces counters ge100-1/1/1.134


.. **Help line:** clear access-list counters

**Command History**

+-------------+---------------------------------------+
|             |                                       |
| Release     | Modification                          |
+=============+=======================================+
|             |                                       |
| 5.1.0       | Command introduced                    |
+-------------+---------------------------------------+
|             |                                       |
| 6.0         | Replaced interface with interfaces    |
+-------------+---------------------------------------+