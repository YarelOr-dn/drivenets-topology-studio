show system stack
-----------------

**Minimum user role:** viewer

T0 display Current, Revert and Target stacks.

**Command syntax: show system stack**

**Command mode:** GI

.. **Note:**

**Example**
::

	gi# show system stack


	  | Component       | HW Model      | HW Revision   | Revert      | Current     | Target        |
	  |-----------------+---------------+---------------+-------------+-------------+---------------|
	  | DNOS            |     -         |     -         | 13.0.2      | 14.0.1      | 15.1.0        |
	  | BaseOS          |     -         |     -         | 1.507       | 2.304       | 2.506         |
	  | NCM-NOS         |     -         |     _         | 2.1.0       | 3.0.0       | 4.0.0         |
	  | Firmware        | S9700-53DX    | 1             | -           | 7.80        | 8.0           |
	  | Firmware        | S9700-23D-J   | 3             | -           | 7.80        | 8.0           |

.. **Help line:** Show current, revert and target stacks.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
