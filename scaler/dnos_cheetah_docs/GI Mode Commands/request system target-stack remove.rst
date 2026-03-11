request system target-stack remove
----------------------------------

**Minimum user role:** admin

Removes packages from the target stack.

- Deletes DNOS, BaseOS, NCM NOS, GI package from the target stack for all node types in a cluster

- For ONIE and firmware package, deletes target stack entries with the specified HW model/revision. Deletes the package from matching HW nodes.
 	- If HW model not specified, deletes all existing ONIE/firmware packages in target stack
	- If HW revision not specified, deletes all matching HW model ONIE/firmware packages existing in target stack

- Not supported when the system is upgrading or reverting.

- Not supported when the system is changing target stack.

- Asynchronous, shows progress.

**Command syntax: request system target-stack remove {dnos \| baseos \| ncm-nos \| gi  \| { {onie \| firmware}** {hardware-model [hw-model] | hardware-model [hw-model] hardware-revision [hw-revision]} }


**Command mode:** GI


**Example**
::

    dnRouter# request system target-stack remove ncm-nos
	NCM-NOS 12.1 package will be removed from target stack.
	Warning: Do you want to continue? (Yes/No) [No]?
	Removed NCM NOS package from target stack

	dnRouter# request system target-stack remove firmware hardware-model S9700-53DX hardware-revision 4
	Firmware for HW model S9700-53DX revision 4 will be removed from target stack
	Warning: Do you want to continue? (Yes/No) [No]?
	Removed firmware package for S9700-53DX revision 4 from target stack


**Note:**

-  Yes/no validation should exist for the operation.

.. **Help line:** Remove package from target stack.


**Parameter table:**

+----------------------+------------------------------------------+----------------------------------------------+---------------+
| Parameter            | Description                              |  Values                                      | Default value |
+======================+==========================================+==============================================+===============+
| hw-model             | The Hardware model                       |                                              | \-            |
+----------------------+------------------------------------------+----------------------------------------------+---------------+
| hw-revision          | The Hardware revision                    |                                              | \-            |
+----------------------+------------------------------------------+----------------------------------------------+---------------+

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+