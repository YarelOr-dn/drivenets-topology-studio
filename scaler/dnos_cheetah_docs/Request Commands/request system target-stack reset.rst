request system target-stack reset
----------------------------------

**Minimum user role:** admin

Align all the software from system target-stack with the software in systen current-stack for any node type in system.

- Not supported when a package is being added or removed.

**Command syntax: request system target-stack reset**

**Command mode:** operational

**Example**
::

	dnRouter# request system target-stack reset
	Warning: Are you sure you want to reset all the software from the target stack? (Yes/No) [No]?

	# Reset all software from the target stack to match the current stack
    dnRouter#

**Note:**

-  Yes/no validation should exist for the operation.

.. **Help line:** Reset all software from the system target-stack.

.. **Parameter table:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 18.2.1        | Command introduced  |
+-------------+-----------------------+