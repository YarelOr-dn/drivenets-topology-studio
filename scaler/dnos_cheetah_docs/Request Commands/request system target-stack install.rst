request system target-stack install
------------------------------------

**Minimum user role:** admin

Updates software/firmware on system nodes to versions in the target stack.

- On each node updates software relevant to the node:
	- DNOS and BaseOS on NCC/NCP/NCF nodes
	- NCM-NOS on NCM nodes
	- GI image on NCC/NCP/NCF nodes
	- ONIE and firmware on the nodes of the HW model and revision specified in the package metadata, or by a user.

**Note:**

- Not supported if the update might violate any version dependency, e.g. if the target DNOS cannot run on the target BaseOS, or if there is no target BaseOS and target GI image cannot run on current BaseOS.

- Not supported when the system is updating or reverting any software on any node.

- Not supported when the system is changing target stack or syncing it to any node.

- Shows progress. Pressing Ctrl+C stops the show and returns prompt; the process continues in background.

**Command syntax: request system target-stack install**

**Command mode:** operational

**Example**
::

	dnRouter# request system target-stack install
	The following software or firmware will be installed:
	   Firmware:
	   	HW platform: S9700-53DX, revision 1, version 4.5, affected nodes: NCP 1,5,10-40
	   	HW platform: S9700-23DJ, revision 2, version 4.6-ab, affected nodes: NCP 0,2-4,6-9,41-47
	   NCM NOS:
	   	Version 12.1, affected nodes: NCM A0, A1
	Do you want to continue? (Yes/No) [No]?

	WARNING! NO NCM REDUNDANCY - NCM B0 IS NOT IN UP STATE!
	WARNING! SYSTEM BACKPLANE CONTROL CONNECTIVITY ISSUE!
		NCM-A0: NCF 1, NCP 2,3 connection state is not "ok"!
	Warning: Do you want to continue? (Yes/No) [No]?


.. **Help line:** Install software target stack on the system.

.. **Parameter table:**

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
