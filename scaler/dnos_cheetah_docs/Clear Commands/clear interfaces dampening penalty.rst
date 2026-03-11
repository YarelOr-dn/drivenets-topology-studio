clear interfaces dampening penalty
----------------------------------

**Minimum user role:** operator

This clear action returns the penalty value to zero. This action always results in bringing the interface back up if it is down because of dampening.

To clear the interface dampening penalty:

**Command syntax: clear interfaces dampening penalty** [interface-name]

**Command mode:** operation

.. **Hierarchies**

**Note**

Clearing the penalty parameter will always result in bringing the interface up if the reason it is down is dampening.

.. - **Clear interfaces dampening** - clears dampening penalty value to zero for **ALL** interfaces

.. - **Clear interfaces dampening interface x** - clears dampening penalty value to zero for a specific interface.

**Parameter table:**

+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+-------------+
|                   |                                                                                                                                                        |                                 |             |
| Parameter         | Description                                                                                                                                            | Range                           | Default     |
+===================+========================================================================================================================================================+=================================+=============+
|                   |                                                                                                                                                        | ge<interface speed>-<A>/<B>/<C> | \-          |
| interface-name    | Clears the penalty value for a specific interface only. If an interface-name is not specified, the penalty value is cleared for all interfaces.        |                                 |             |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+-------------+

**Example**
::

	dnRouter# clear interfaces dampening penalty
	dnRouter# clear interfaces dampening penalty ge100-1/0/1


.. **Help line:** clear interface dampening penalty

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+