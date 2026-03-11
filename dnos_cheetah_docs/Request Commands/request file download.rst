request file download 
----------------------

**Minimum user role:** operator

To copy file to the Network Cloud server from an external server:

**Command syntax: request file download** [user-name]@ **[url] [file-type] [file-name]** out-of-band

**Command mode:** operational

**Note**

- If you do not specify an ncc-id/ncp-id/ncf-id/ncm-id, the command relates to the active NCC.

- Each file type resides in a different location in the server:

	- Log - /var/log/dn/

	- Core - /core/

	- Tech-support - /techsupport/

	- Config - /config/

	- Rollback - /rollback/

	- Traces - /var/log/dn/traces

	- Certificate - /security/cert/

	- Key - /security/key/

	- Measured-boot - /security/measured-boot/

	- Event-policy - /event-manager/event-policy/scripts/

	- Periodic-policy - /event-manager/periodic-policy/scripts/

	- Generic-policy - /event-manager/generic-policy/scripts/

- The command can only be used with the SCP protocol. FTP Client and TFTP are not supported.

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+------------------+
| Parameter | Description                                                                                                                                    | Range                  | Default          |
+===========+================================================================================================================================================+========================+==================+
| user-name | Optional. The name of the user performing the operation. By default, this will be the current user.                                            | String                 | The current user |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+------------------+
| url       | The location and new file name. Specifying a filename that is different from the source file name, renames the file in the destination folder. | host://source-filename | \-               |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+------------------+
| file-type | The type of file to download                                                                                                                   | log                    | \-               |
|           |                                                                                                                                                | core                   |                  |
|           |                                                                                                                                                | tech-support           |                  |
|           |                                                                                                                                                | config                 |                  |
|           |                                                                                                                                                | certificate            |                  |
|           |                                                                                                                                                | key                    |                  |
|           |                                                                                                                                                | measured-boot          |                  |
|           |                                                                                                                                                | event-policy           |                  |
|           |                                                                                                                                                | periodic-policy        |                  |
|           |                                                                                                                                                | generic-policy         |                  |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+------------------+
| file-name | The name of the file being downloaded, including suffixes.                                                                                     | String                 | \-               |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+------------------+

**Example**
::

	dnRouter# request file download user@192.168.1.1://myConfig myLocalConfig 
	File loading ...100%
	

.. **Help line:** download file from remote location

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1.0   | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Syntax change                                                      |
+---------+--------------------------------------------------------------------+
| 11.0    | Added support for file types                                       |
+---------+--------------------------------------------------------------------+
| 11.2    | Added security certificate                                         |
+---------+--------------------------------------------------------------------+
| 11.6    | Added source-interface                                             |
+---------+--------------------------------------------------------------------+
| 13.1    | Added file types - Event-policy / Periodic-policy / Generic-policy |
+---------+--------------------------------------------------------------------+
| 19.2    | Added file type - measured-boot                                    |
+---------+--------------------------------------------------------------------+