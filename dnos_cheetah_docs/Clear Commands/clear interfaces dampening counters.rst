clear interfaces dampening counters
-----------------------------------

**Minimum user role:** operator

This clear action returns the penalty value to zero. This action always results in bringing the interface back up if it is down because of dampening.

To clear the interface dampening counters:

**Command syntax: clear interfaces dampening counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

.. - **Clear interfaces dampening** - clears dampening counters for **ALL** interfaces

.. - **Clear interfaces dampening interface x** - clears dampening counters value to zero for a specific interface.

**Parameter table:**

+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+-------------+
|                   |                                                                                                                                                        |                                 |             |
| Parameter         | Description                                                                                                                                            | Range                           | Default     |
+===================+========================================================================================================================================================+=================================+=============+
|                   |                                                                                                                                                        | ge<interface speed>-<A>/<B>/<C> | \-          |
| interface-name    | Clears the dampening counters for a specific interface only. If an interface-name is not specified, the counters are cleared for all interfaces.       |                                 |             |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+-------------+



**Example**
::

	dnRouter# clear interfaces dampening counters
	dnRouter# clear interfaces dampening counters ge100-1/0/1

.. **Help line:** Clear interface dampening counters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+