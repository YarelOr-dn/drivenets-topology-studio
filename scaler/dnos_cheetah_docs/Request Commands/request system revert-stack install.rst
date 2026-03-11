request system revert-stack install
------------------------------------

**Minimum user role:** admin

Reverts the system software to versions in the revert stack.

**Command syntax: request system revert-stack install**

**Command mode:** operational

**Example**
::

	dnRouter# request system revert-stack install
	The system will revert to the following software:
	   NCM NOS 12.1, affected nodes: NCM A0, A1
	Warning: Do you want to continue? (Yes/No) [No]?

	WARNING! NO NCM REDUNDANCY - NCM B0 IS NOT IN UP STATE!
	WARNING! SYSTEM BACKPLANE CONTROL CONNECTIVITY ISSUE!
		NCM-A0: NCF 1,2, NCP 2 connection state is not "ok"!
	Warning: Do you want to continue? (Yes/No) [No]?


**Note:**

- Firmware and ONIE are not reverted.

- Not supported when the system is updating or reverting any software on any node.

- Shows progress until node reboot or until user presses Ctrl+C which stops the show. The process continues in the background.

- Yes/no validation should exist for the operation.

- Double confirmation should be requested if NCMs in "up" state are not redundant, or if backplane control connectivity of enabled NCP/F node is not "ok".


.. **Help line:** Revert system software to versions in the revert stack.

.. **Parameter table:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
