request uefi key delete
-----------------------

**Minimum user role:** admin

Delete the key from the UEFI key list.

**Command syntax: request uefi key delete** { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} **[key-type] [key-file]**

**Command mode:** operational

**Note:**

- Validation : User Yes/no question with the specified key file name.

- If no ncc-id/ncp-id/ncf-id/ncm-id is specified, the command will address the active NCC.

- An error message is returned when the specified node type or node id are unavailable or not supported.

- Key types:

 -  pk - platform key

 -  kek - key exchange key

 -  db - authorized database key

 -  dbx - forbidden database key

- Key file - path to file holding the requested key to remove from the key list

**Parameter table:**

+-----------+-----------------------------------------------+---------------+
| Parameter | Values                                        | Default value |
+===========+===============================================+===============+
| key-type  | pk / kek / db / dbx                           |               |
+-----------+-----------------------------------------------+---------------+
| key-file  | string. Including sub-directory (/)           |               |
+-----------+-----------------------------------------------+---------------+
| ncc-id    | 0-1                                           |               |
+-----------+-----------------------------------------------+---------------+
| ncp-id    | integer                                       |               |
+-----------+-----------------------------------------------+---------------+
| ncf-id    | integer                                       |               |
+-----------+-----------------------------------------------+---------------+
| ncm       | a0, b0, a1, b1                                |               |
+-----------+-----------------------------------------------+---------------+

**Example**
::

	dnRouter# request uefi key delete pk /config/keys/pk.auth
	Are you sure you want to delete /config/keys/pk.auth (Yes/No) [No]? Yes
	Key successfully deleted from key list.	

	dnRouter# request uefi key delete pk /config/keys/pk.auth
	Are you sure you want to delete /config/keys/pk.auth (Yes/No) [No]? Yes
	Error: failed to delete key from key list.	

	dnRouter# request uefi key delete ncp 0 kek /config/keys/kek.auth
	Are you sure you want to delete /config/keys/kek.auth (Yes/No) [No]?

	dnRouter# request uefi key delete ncp 1 kek /config/keys/kek.auth
	Error: node type or node id unavailable or not supported.


**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 19.2    | Command introduced                  |
+---------+-------------------------------------+