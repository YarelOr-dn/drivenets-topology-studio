request system target-stack reset
---------------------------------

**Minimum user role:** viewer

Resets all the software/firmware from the target stack.

**Command syntax: request system target-stack reset**

**Command mode:** GI

**Note**

- Not supported when the target stack is modified.


**Example**
::

	gi# request system target-stack reset
	Warning: Are you sure you want to reset all the software from the target stack? (Yes/No) [No]?

	# Reset all software from the target stack to match the current stack
	gi#


.. **Hidden Note:**

 -  Yes/no validation should exist for the operation.


.. **Parameter table:**


.. **Help line:** Reset target-stack.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2.1    | Command introduced                |
+---------+-------------------------------------+