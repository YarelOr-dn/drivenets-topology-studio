show pim ranges
---------------

**Minimum user role:** viewer

You can use this command to display the PIM IP ranges for PIM-ASM, PIM-SSM, MoFRR and Boundary.



**Command syntax:show pim ranges**

**Command mode:** operational



**Note**

- SSM overrides ASM by default.

.. - Overrides: describe the override policy - SSM overrides ASM by default



**Example**
::

	dnRouter# show pim ranges

	SSM-Ranges:
		232.0.0.0/8
		239.2.3.0/24
	ASM Ranges:
		224.0.0.0/4
	Override: SSM overrides ASM
	MoFRR Ranges: 
		232.0.2.0/24
		225.1.0.0/16
	Boundary:
		Interface ge100-0/0/1.2:
			Ranges:
				228.1.3.0/24
				226.1.0.0/8

		Interface bundle-1.20:
			Ranges: 227.2.34.0/24


	dnRouter# show pim ranges

	SSM-Ranges:
		232.0.0.0/8
		239.2.3.0/24
	ASM Ranges:
		224.0.0.0/4
	Override: ASM overrides SSM
	MoFRR Ranges:
		232.0.2.0/24
		225.1.0.0/16
	Boundary:
		Interface bundle-1.20:
			Ranges:
				227.2.34.0/24

.. **Help line:** Show PIM IP ranges for PIM-ASM, PIM-SSM, MoFRR and Boundary

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 12.0    | Command introduced    |
+---------+-----------------------+
| 14.0    | Updated MoFRR support |
+---------+-----------------------+
