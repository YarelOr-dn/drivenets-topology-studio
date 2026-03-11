request system target-stack install
-----------------------------------

**Minimum user role:** viewer

Updates the system software/firmware to versions in the target stack.

**Command syntax: request system target-stack install**

**Command mode:** GI

**Note**

- Updates DNOS, BaseOS, GI, ONIE, and firmware on the node.

- Starts DNOS which in cluster should continue update of other HW nodes.

- Not supported if the update would violate any version dependency, e.g. if target DNOS cannot run on target BaseOS, or if there is no target BaseOS and target GI image cannot run on current BaseOS.

- Not supported when the system is updating or reverting any software.

- Not supported when the system is changing target stack.

- Shows progress until node reboot or until user presses Ctrl C which stops the show. The process continues in background.


**Example**
::

	gi# request system target-stack install
	The following software or firmware will be installed:
	   Firmware:
	   	HW platform: S9700-53DX, revision 1, version 4.5
	   	HW platform: S9700-23DJ, revision 2, version 4.6-ab
	   NCM NOS 12.1
	   BaseOS 1.687
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, installation will run in background.
	Started target stack installation, task ID = 8.
	Started BaseOS installation on NCC 0, task ID = 81
	Rebooting...

	gi# request system target-stack install
	The following software or firmware will be installed:
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, installation will run in background.
	Started target stack installation, task ID = 8.
	Started DNOS deployment on NCC 0, task ID = 81
	Finished DNOS deployment on NCC 0, task ID = 81
	Entering DNOS mode.


.. **Hidden Note:**

 - Yes/no validation should exist for the operation.


.. **Parameter table:**


.. **Help line:** Install target stack on the system.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
