request system target-stack load
--------------------------------

**Minimum user role:** viewer

Loads a package from a local system location or via a HTTP(s) GET from a remote location and adds it to the target stack.

A Package can contain software of one of the following types, or it can be a bundle of a few such packages:

- DNOS

- BaseOS

- NCM NOS

- Firmware for specific HW models and revisions

- ONIE image for specific HW model and revision

- GI image.

**Command syntax: request system target-stack load [file-name | url]** hardware-model [hw-model] hardware-revision [hw-revision]

**Command mode:** GI

**Note**

- User input must start with "file://" to indicate the file path or "http://" to invoke HTTP GET

 - If the user enters [file-name | url] without the expected "file://", or "http://",  an error message is displayed: "ERROR: Unknown word, must enter file path or url"
 - If the file does not exist, an error message is displayed: "ERROR: No such file or directory"
 - If http fails to connect, an error message is displayed: "ERROR: The connection has timed out"

-  When a user enters a file path, the user can point to any file on any path on the host system

-  Yes/no validation should exist for the operation.

-  If a node connects, the system syncs the target stack to the node (only software which is relevant to the node type and HW)

-  In case of file-name, package will be loaded from the DNOS folder.


**Example**
::

 gi# request system target-stack load http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar

	Package http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar will be downloaded and added to target stack.
	Warning: Do you want to continue? (Yes/No) [No]?
	started target-stack load NCC 0, task ID = 99

	Press Ctrl C to exit progress show, operation will run in background.
	Download in progress ...
	Download finished...
	Added NCM NOS version 1.1.0 to target stack.


	gi# request system target-stack load file://techsupport/packages/drivenets_stratax_1.1.0.tar

	Package drivenets_stratax_1.1.0.tar will be loaded and added to target stack.
	Warning: Do you want to continue? (Yes/No) [No]?
	started target-stack load NCC 0, task ID = 100

	Added NCM NOS version 1.1.0 to target stack.



	gi# request system target-stack load file://tmp/ufi-wbx-fw-17-0 hardware-model S9700-53DX hardware-revision 4

	Package ufi-wbx-fw-17-0 will be loaded and added to target stack for HW model S9700-53DX, revision 4.
	Warning: Do you want to continue? (Yes/No) [No]?
	started target-stack load NCC 0, task ID = 101

	Added firmware version 4.5 for HW model S9700-53DX, revision 4 to target stack.



.. **Hidden Note:**

 - After a package is untared, the package metadata is inspected to understand which software it contains.

 - For firmware and ONIE packages a user may set the intended HW model and revision instead of those specified in the package metadata. Revision may be "default", meaning all the revisions of this HW model for which no package is set explicitly. For other package types, HW model/revision parameters are ignored.

 - The command will fail if a bundle package contains multiple packages of the same type.

 - Each package replaces a previous package of the same type in the target stack, if exists.

 - Verifies Drivenets signature on a package.

 - If firmware package was delivered directly by the HW vendor without Drivenets signature, a user may provide MD5 hash for verification; otherwise the package won't be verified. It's highly recommended to provide a hash received from the HW vendor to ensure package integrity and authenticity. Installing an unverified package may compromise system security. Corrupted firmware may cause HW malfunction.

 - In a cluster, the active NCC replicates the target stack to the standby NCC.

 - In a cluster, the active NCC syncs the target stack to all the connected nodes - copies DNOS, BaseOS, GI images to all the NCP/NCF nodes, NCM NOS to all the NCMs, firmware and ONIE to all the nodes of the HW model/revision set for the package.

 - Not supported when the system is upgrading or reverting.

 - Not supported when the system is changing target stack.

 - Shows progress. Pressing Ctrl+C stops the show and returns prompt, the process continues in background.


**Parameter table:**

+-------------+-------------------------------------------------+--------------------------------+---------+
|  Parameter  | Description                                     |              Range             | Default |
+=============+=================================================+================================+=========+
| url         | The URL of the package                          | Will start with http:// prefix | /-      |
+-------------+-------------------------------------------------+--------------------------------+---------+
| file-name   | The URL of the package                          | Will start with file:// prefix | /-      |
+-------------+-------------------------------------------------+--------------------------------+---------+
| hw-model    | The hardware model for ONIE/firmware package    |                                | /-      |
+-------------+-------------------------------------------------+--------------------------------+---------+
| hw-revision | The hardware revision for ONIE/firmware package |                                | default |
+-------------+-------------------------------------------------+--------------------------------+---------+

.. **Help line:** Load software/firmware to target stack.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
