request system target-stack clear
---------------------------------

**Minimum user role:** viewer

Reverts all software/firmware from the target stack.

**Command syntax: request system target-stack clear**

**Command mode:** GI

**Note**

- Not supported when the system is upgrading or reverting.

- Not supported when the target stack is modified.


**Example**
::

	gi# request system target-stack clear
	Warning: Are you sure you want to remove all the software from the target stack? (Yes/No) [No]?

	# Removed all software from the target stack
	gi#


.. **Hidden Note:**

 -  Yes/no validation should exist for the operation.


.. **Parameter table:**


.. **Help line:** Clear target-stack.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
