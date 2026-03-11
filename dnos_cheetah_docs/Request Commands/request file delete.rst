request file delete
--------------------

**Minimum user role:** admin

Delete the file from the local directory.

**Command syntax: request file delete** { ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} **[file-type] [file-name]**

**Command mode:** operational

**Note:**

- Validation : User Yes/no question with the specified file name.

- User cannot delete the current in use log file (log.0).

- If no ncc-id/ncp-id/ncf-id/ncm-id was specified, the command relates to the active NCC.

- File types locations:

 -  config - /config/

 -  log - /var/log/dn/

 -  core - /core/

 -  tech-support - /techsupport/

 -  certificate -  /security/cert/

 -  key -  /security/key/

 -  event-policy - /event-manager/event-policy/scripts/

 -  periodic-policy - /event-manager/periodic-policy/scripts/

 -  generic-policy - /event-manager/generic-policy/scripts/

 -  packet-capture - /packet-capture/

 -  integrity-report-retrieves - /core/integrity_report_retrieves

- File types to delete from the NCCs:

 -  config

 -  log

 -  traces

 -  core

 -  tech-support

 -  security

 -  event-policy

 -  periodic-policy

 -  generic-policy

 -  packet-capture

 -  integrity-report-retrieves

- File types to delete from the NCPs/NCFs:

 -  log

 -  traces

 -  core

- File types to delete files on the NCMs:

 -  log

 -  config

 -  core

 -  tech-support

- For file type "packet-capture", support for the active NCC only.

**Parameter table:**

+-----------+-----------------------------------------------+---------------+
| Parameter | Values                                        | Default value |
+===========+===============================================+===============+
| file-type | log / traces / config / core / tech-support / |               |
|           | integrity-report-retrieves                    |               |
|           |                                               |               |
|           | security - supported in v11.1                 |               |
|           | / event-policy / periodic-policy              |               |
|           | / generic-policy / packet-capture             |               |
+-----------+-----------------------------------------------+---------------+
| file-name | string. Including sub-directory (/)           |               |
+-----------+-----------------------------------------------+---------------+
| ncc-id    | 0-1                                           |               |
+-----------+-----------------------------------------------+---------------+
| ncp-id    | 0-191                                         |               |
+-----------+-----------------------------------------------+---------------+
| ncf-id    | 0-12                                          |               |
+-----------+-----------------------------------------------+---------------+
| ncm       | a0, b0, a1, b1                                |               |
+-----------+-----------------------------------------------+---------------+

**Example**
::

	dnRouter# request file delete config MyConfig.txt
	Are you sure you want to delete MyConfig.txt (Yes/No) [No]?


	dnRouter# request file delete packet-capture BGP_Debug.1.pcap
	Are you sure you want to delete BGP_Debug.1.pcap (Yes/No) [No]?


**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+