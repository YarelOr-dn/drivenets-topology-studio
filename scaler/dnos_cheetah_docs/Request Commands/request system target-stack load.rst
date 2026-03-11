request system target-stack load
--------------------------------

**Minimum user role:** admin

Loads packages from the DNOS local system location or via HTTP(s) GET from remote location and adds it to the target stack.

- A package can contain software of one of the following types, or it can be a bundle of few such packages:
	- DNOS
	- BaseOS
	- NCM NOS
	- Firmware for specific HW models and revisions
	- ONIE image for specific HW model and revision
	- GI image.

- After a package is untared, inspect package metadata to understand which software it contains.

- For firmware and ONIE packages a user may set the intended HW model and revision instead of those specified in the package metadata. Revision may be "default", meaning all the revisions of this HW model for which no package is set explicitly. For other package types HW model/revision parameters are ignored.

- Command fails if a bundle package contains a few packages of the same type.

- Each package replaces the previous package of the same type in the target stack, if exists.

- Verifies Drivenets signature on a package.

- If a firmware package was delivered directly by the HW vendor without the a Drivenets signature, a user may provide the MD5 hash for verification; otherwise the package won't be verified. It's highly recommended to provide a hash received from the HW vendor to ensure package integrity and authenticity. Installing an unverified package may compromise system security. Corrupted firmware may cause HW malfunction.

- In a cluster, the active NCC replicates a target stack to the standby NCC.

- In a cluster, the active NCC syncs a target stack to all the connected nodes - copies DNOS, BaseOS, GI images to all the NCP/NCF nodes, NCM NOS to all the NCMs, firmware and ONIE to all the nodes of the HW model/revision set for the package.

- Not supported when the system is upgrading or reverting.

- Not supported when the system is changing target stack.

**Command syntax: request system target-stack load ([url] /| [file-name] \| inband)** [url] \| hw-model [hw-model] \| hw-revision [hw-revision]

**Command mode:** operational

**Example**
::
dnRouter# request system target-stack load http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar

Package http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar will be downloaded and added to target stack.
Warning: Do you want to continue? (Yes/No) [No]?
started target-stack load NCC 0, task ID = 99

dnRouter# request system target-stack load http://172.16.100.12/packages/ufi-wbx-fw-17-0 hardware-model S9700-53DX hardware-revision 4

Package http://172.16.100.12/packages/ufi-wbx-fw-17-0 will be downloaded and added to target stack for HW model S9700-53DX, revision 4.
Warning: Do you want to continue? (Yes/No) [No]?
started target-stack load NCC 0, task ID = 100

dnRouter# request system target-stack load file://techsupport/drivenets_stratax_1.1.0.tar

Package drivenets_stratax_1.1.0.tar will be loaded and added to target stack.
Warning: Do you want to continue? (Yes/No) [No]?
started target-stack load NCC 0, task ID = 101

Added NCM NOS version 1.1.0 to target stack.



dnRouter# request system target-stack load file://techsupport/ufi-wbx-fw-17-0 hardware-model S9700-53DX hardware-revision 4

Package ufi-wbx-fw-17-0 will be loaded and added to target stack for HW model S9700-53DX, revision 4.
Warning: Do you want to continue? (Yes/No) [No]?
started target-stack load NCC 0, task ID = 99

Added firmware version 4.5 for HW model S9700-53DX, revision 4 to target stack.

dnRouter# request system target-stack load inband http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar

Package http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar will be downloaded and added to target stack.
Warning: Do you want to continue? (Yes/No) [No]?
started target-stack load NCC 0, task ID = 99

**Note:**

-  User input must start with "file://" to indicate file path or "http://" to invoke HTTP GET
	- If user entered [file-name | url] without expected "file://", or "http://",  display error message: "ERROR: Unknown word."
	- If file does not exist, display error message: "ERROR: No such file or directory"
	- If http fail to connect, display error message: "ERROR: The connection has timed out"

-  When user enter a file path, user can point to any file on volume mounted to the DNOS containers

-  Yes/no validation should exist for the operation.

-  If a node connects, system syncs target stack to the node (only software which is relevant to the node type and HW).

-  In case of file-name package will be loaded from the DNOS folder.

-  In case inband is used, the target stack will be downloaded over the in-band management VRF as were set by the "system in-band-management dnor-server-vrf" command
    - in case "system in-band-management dnor-server-vrf" is configured with non-default IB management VRF, the source-interface that will be used is according to the interface that is configured under "network-services vrf instance in-band-management source-interface" of the same non-default IB management VRF

.. **Help line:** Load software/firmware to target stack.

**Parameter table:**

+----------------------+-----------------------------------------------+-------------+---------------+
| Parameter            | Description                                   | Ranges      | Default value |
+======================+===============================================+=============================+
| url                  | Package URL (will start with http:// prefix)  |             | \-            |
+----------------------+-----------------------------------------------+-------------+---------------+
| file-name            | Package URL (will start with file:// prefix)  |             | \-            |
+----------------------+-----------------------------------------------+-------------+---------------+
| hw-model             | Hardware model for ONIE/firmware package      |             | \-            |
+----------------------+-----------------------------------------------+-------------+---------------+
| hw-revision          | Hardware revision for ONIE/firmware package   |             |      default  |
+----------------------+-----------------------------------------------+-------------+---------------+
| inband               | Indicates if the download will be done via IB |             |               |
+----------------------+-----------------------------------------------+-------------+---------------+

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
