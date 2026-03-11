request system target-stack clear
----------------------------------

**Minimum user role:** admin

Removes all the software from system target-stack for any node type in system

- Not supported when the system is upgrading or reverting.

- Not supported when a package is being added or removed.

**Command syntax: request system target-stack clear**

**Command mode:** operational

**Example**
::

	dnRouter# request system target-stack clean
	Warning: Are you sure you want to remove all the software from the target stack? (Yes/No) [No]?

	# Removed all software from the target stack
    dnRouter#

**Note:**

-  Yes/no validation should exist for the operation.

.. **Help line:** Remove all software from the system target-stack.

.. **Parameter table:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
