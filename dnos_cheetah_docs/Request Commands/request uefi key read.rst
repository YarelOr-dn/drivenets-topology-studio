request uefi key read
---------------------

**Minimum user role:** admin

Read out specified key-list.

**Command syntax: request uefi key read** { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} **[key-list] [key-list-file]**

**Command mode:** operational

**Note:**

- If no ncc-id/ncp-id/ncf-id/ncm-id is specified, the command will address the active NCC.

- An error message is returned when the specified node type or node id are unavailable or not supported.

- Key lists:

 -  pk - platform key list

 -  kek - key exchange key list

 -  db - authorized database key list

 -  dbx - forbidden database key list

- Key list file - path to file that will be used for saving the read key list.

**Parameter table:**

+----------------+-----------------------------------------------+---------------+
| Parameter      | Values                                        | Default value |
+================+===============================================+===============+
| key-list       | pk / kek / db / dbx                           |               |
+----------------+-----------------------------------------------+---------------+
| key-list-file  | string. Including sub-directory (/)           |               |
+----------------+-----------------------------------------------+---------------+
| ncc-id         | 0-1                                           |               |
+----------------+-----------------------------------------------+---------------+
| ncp-id         | integer                                       |               |
+----------------+-----------------------------------------------+---------------+
| ncf-id         | integer                                       |               |
+----------------+-----------------------------------------------+---------------+
| ncm            | a0, b0, a1, b1                                |               |
+----------------+-----------------------------------------------+---------------+

**Example**
::

	dnRouter# request uefi key read pk /config/keys/pk.list
	Key list successfully read.

	dnRouter# request uefi key read pk /config/keys/pk.list
	Error: failed to read key list.	

	dnRouter# request uefi key read ncp 0 dbx /config/keys/dbx.list
	Key list successfully read.

	dnRouter# request uefi key read ncp 1 kek /config/keys/kek.auth
	Error: node type or node id unavailable or not supported.

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 19.2    | Command introduced                                                 |
+---------+--------------------------------------------------------------------+