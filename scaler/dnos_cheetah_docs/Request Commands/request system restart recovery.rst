request system restart recovery 
--------------------------------

**Minimum user role:** techsupport

Use this command to enter recovery mode. 

In recovery mode, you can perform the following commands:

- "request system restart"

- "request system restart factory-default"

- "request system restart rollback"

**Command syntax: request system restart** recovery

**Command mode:** operational

**Note**

- Exiting recovery mode requires system restart.


..
	**Internal Note**

	- Yes/no validation should exist for system restart operations

**Example**
::

	dnRouter# request system restart recovery
	Warning: Are you sure you want to switch to recovery mode? Operation will cause system restart (Yes/No) [No]? 
 
.. **Help line:** request system to enter recovery mode

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+