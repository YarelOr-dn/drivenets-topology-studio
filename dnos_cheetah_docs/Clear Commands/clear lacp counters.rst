clear lacp counters
--------------------

**Minimum user role:** operator

Clearing the LACP interface counters resets the counters to zero and removes the counter information from the database.

To clear the LACP interface counters:

**Command syntax: clear lacp counters [interface-name]**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - **Clear lacp counters** - clears all counters for **ALL** interfaces

 - **Clear lacp counters interface [bundle interface]** - clears all counters for all members in the bundle

 - **Clear lacp counters interface [physical interface]** - clears all counters for a specific member interface


**Parameter table:**

+-------------------+------------------------------------------------------------------------------------------------------+---------------------------------+-------------+
|                   |                                                                                                      |                                 |             |
| Parameter         | Description                                                                                          | Range                           | Default     |
+===================+======================================================================================================+=================================+=============+
|                   |                                                                                                      |                                 |             |
| interface-name    | optionally specify an interface name to clear only the LACP counters for the specified interface.    | ge<interface speed>-<A>/<B>/<C> | \-          |
|                   |                                                                                                      |                                 |             |
|                   |                                                                                                      | bundle-<bundle-id>              |             |
+-------------------+------------------------------------------------------------------------------------------------------+---------------------------------+-------------+


**Example**
::

	dnRouter# clear lacp counters
	dnRouter# clear lacp counters bundle-1
	dnRouter# clear lacp counters ge100-1/1/1



.. **Help line:** clear lacp counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+