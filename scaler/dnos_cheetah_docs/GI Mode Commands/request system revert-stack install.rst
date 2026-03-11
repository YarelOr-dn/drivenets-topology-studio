request system revert-stack install
-----------------------------------

**Minimum user role:** viewer

Reverts the system software to a version in the revert stack.

**Command syntax: request system revert-stack install**

**Command mode:** GI

**Note**

- Firmware and ONIE are not reverted.

- Not supported when the system is updating or reverting any software.

- Shows progress until node reboot or until the user presses Ctrl+C which stops the show. The process continues in the background.


**Example**
::

	gi# request system revert-stack install
	The system will revert to the following software:
	   NCM NOS 12.1
	   BaseOS 1.687
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, installation will run in background.
	Started revert stack installation, task ID = 8.
	Started BaseOS revert on NCC 0, task ID = 81
	Rebooting...

	gi# request system revert-stack install
	The system will revert to the following software:
	   DNOS 17.2
	Warning:  Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, installation will run in background.
	Started revert stack installation, task ID = 8.
	Started DNOS deployment on NCC 0, task ID = 81
	Finished DNOS deployment on NCC 0, task ID = 81
	Entering DNOS mode.


.. **Hidden Note:**

 - Yes/no validation should exist for the operation.


.. **Parameter table:**


.. **Help line:** Revert system software to versions in the revert stack.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
