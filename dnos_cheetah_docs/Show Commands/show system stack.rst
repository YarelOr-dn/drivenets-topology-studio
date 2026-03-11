show system stack
--------------------

**Command syntax: show system stack** 

**Description:** Displays current, revert and target stacks. 

**CLI example:**
::

	dnRouter# show system stack 
	
	
	  | Component       | HW Model      | HW Revision   | Revert      | Current     | Target                |
	  |-----------------+---------------+---------------+-------------+-------------+-----------------------|
	  | DNOS            |     -         |     -         | 13.0.2      | 14.0.1      | 15.1.0                |
	  | BaseOS          |     -         |     -         | 1.507       | 2.304       | 2.506                 |
	  | NCM-NOS         |     -         |     _         | 2.45        | 3.50        | 4.0                   |
	  | Firmware        | S9700-53DX    | 1             | -           | 7.80        | 8.0                   |
	  | Firmware        | S9700-23D-J   | 3             | -           | 7.80        | 8.0                   |


**Command mode:** operational

**TACACS role:** viewer

**Note:**


**Help line:** Show current, revert and target stacks. 

**Outputs table:**