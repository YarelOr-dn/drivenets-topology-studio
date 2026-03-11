clear isis neighbor
-------------------

**Minimum user role:** operator

To clear the IS-IS database and reset IS-IS adjacencies:

**Command syntax: clear isis** instance [isis-instance-name] **process**

**Command mode:** operation

.. **Hierarchies**

**Note:**

-  Use "instance [isis-instance-name]" to clear from a specific ISIS instance

-  Use "set [system-id]" to reset specific neighbor adjacency

**Parameter table:**

+--------------------+-----------------------------------------------------------------------+-----------------------------------------+
| Parameter          | Description                                                           | Range                                   |
+====================+=======================================================================+=========================================+
| no parameter       | Reset all IS-IS neighbor adjacencies                                  | \-                                      |
+--------------------+-----------------------------------------------------------------------+-----------------------------------------+
| isis-instance-name | Reset all IS-IS neighbor adjacencies for the specified IS-IS instance | 1..255 characters                       |
+--------------------+-----------------------------------------------------------------------+-----------------------------------------+
| system-id          | Resets a specific neighbor adjacency.                                 | ssss.ssss.ssss (where s is a hex value) |
+--------------------+-----------------------------------------------------------------------+-----------------------------------------+

**Example**
::

	dnRouter# clear isis neighbor

	dnRouter# clear isis neighbor 0100.0070.1A45

	dnRouter# clear isis instance ISIS_A neighbor 0100.0070.1A45
	50.0001.F100.0070.1A45.00, 50.0002.F100.0070.1A45.00




.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
