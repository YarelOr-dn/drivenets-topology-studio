request system install retry
----------------------------

**Minimum user role:** viewer

To invoke current stack re-installation on a specific node, for all stack packages:

**Command syntax: request system install retry { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] }**

**Command mode:** GI

**Note**

- In the event of installing a DNOS package on an active NCC, the DNOS in a cluster will continue the update of other HW nodes.

- Shows progress until node reboot or until user presses Ctrl+C which stops the show. The process continues in the background.


**Example**
::

	gi# request system install retry ncc 0
	The following software or firmware will be installed:
	   BaseOS 1.687
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

	Press Ctrl C to exit progress show, installation will run in background.
	Started target stack installation, task ID = 8.
	Started BaseOS installation on NCC 0, task ID = 81
	Rebooting...

.. **Hidden Note:**

 - Yes/no validation should exist for the operation.


.. **Parameter table:**


.. **Help line:** Reinstall current stack on a specific node

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
