request system install retry
----------------------------

**Minimum user role:** admin

Retries software/firmware installation on a node where a previous installation attempt failed.

**Command syntax: request system install retry { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id] }**

**Command mode:** operational

**Example**
::

	dnRouter# request system install retry ncp 3
	Error: installation retry is unavailable!

	dnRouter# request system install retry ncp 4
	The following software or firmware will be installed:
	   Firmware: version 4.6-ab for HW platform S9700-23DJ, revision 2
	   BaseOS 2.304
	   DNOS 16.0.1

	dnRouter# request system install retry ncp 5
	The following software or firmware will be installed:
	   DNOS 16.0.1


**Note:**

- Retry is available for nodes in dnos-deployment(failed) / nos-upgrade(failed) / baseos-upgrade(failed) / firmware-upgrade(failed) / onie-upgrade(failed) / gi-upgrade(failed) / baseos-revert(failed) - If.

.. **Help line:** Retry software/firmware installation on a failed node.

**Parameter table:**

+----------------+--------------------------------+------------------------------------+---------------+
| Parameter      | Description                    | Range                              | Default value |
+================+================================+====================================+===============+
| ncc-id         | The id of the NCC              | 0-1                                | \-            |
+----------------+--------------------------------+------------------------------------+---------------+
| ncp-id         | The id of the NCP              | 0..(Cluster type max NCP number-1) | \-            |
+----------------+--------------------------------+------------------------------------+---------------+
| ncf-id         | The id of the NCF              | 0..(Cluster type max NCF number-1) | \-            |
+----------------+--------------------------------+------------------------------------+---------------+
| ncm-id         | The id of the NCM              | A0, B0, A1, B1                     | \-            |
+----------------+--------------------------------+------------------------------------+---------------+

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 16.1        | Command introduced    |
+-------------+-----------------------+
