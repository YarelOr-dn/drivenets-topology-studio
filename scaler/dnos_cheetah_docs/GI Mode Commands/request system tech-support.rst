request system tech-support
---------------------------

**Minimum user role:** operator

You can generate a file with all the logs, configuration, database files and system output commands that you can save for later use (for example, when opening a customer support case).

After running the command, you will regain full CLI control while the system is generating the tech-support file in the background.

The system can handle only one request to generate a tech-support file at a time. If the system is already creating a tech-support file while you enter another request, an error message will be displayed.

To generate the tech-support file:

**Command syntax: request system tech-support [file-name]** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} after [after-time] before [before-time] password force include {[info-type], [info-type], ...}

**Command mode:** GI

**Note**

- By default, generate tech-support with information from the last 24 hours for rotated logs (end with .1, .2, date, etc.) and always include the latest version of the main logs (logs that are currently being written to) regardless if they were modified in the past 24 hours.

- The Tech-support files are generated on the active NCC node at /techsupport/ Only one file is stored at a time.

- When you generate a tech-support file, a previous file will be deleted to make room for the new file.

.. - User gets back cli prompt after invoking "request system tech-support" user have full CLI support while techsupport is being generated in the background.

	- Tech-support files are generated on active NCC node at /techsupport/

	- tech-support files are generated with user provided filename_HH:MM:SS_DD-MM-YY.tar

	- extended - generate tech-support with core files from both NCCs and all NCPs (under /core)

	- ncp-id - generate tech-support from NCCs and specific NCP only.

	- Only single techsupport request can be handled by DNOS at the same moment. If another request is given while a different tech-support file is currently created, the following message will be displayed "Cannot produce a new techsupport file, another process is already running"

	- Only single techsupport file can be stored at /techsupport at a given moment. Generation of new techsupport file will require deletion of old file.

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| Parameter   | Description                                                                                                                                                                                                                            | Range                                                                                        | Default       |
+=============+========================================================================================================================================================================================================================================+==============================================================================================+===============+
| file-name   | Provide a name for the file. A date suffix is added to the user provided name: _HH:MM:SS_DD-MM-YY.tar                                                                                                                                  | \-                                                                                           | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| password    | Generates the tech-support file with passwords. By default, passwords are removed from the output.                                                                                                                                     | \-                                                                                           | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| force       | Automatically delete a previous tech-support file. By default, you will be prompted to choose whether to delete a previous tech-support file in order to complete the generation of the tech-support file, or to cancel the operation. | \-                                                                                           | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| ncc-id      | Generate the tech-support file with information from the specified NCC only.                                                                                                                                                           | 0..1                                                                                         | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| ncp-id      | Generate the tech-support file with information from the specified NCP only.                                                                                                                                                           | 0..47                                                                                        | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| ncf-id      | Generate the tech-support file with information from the specified NCF only.                                                                                                                                                           | 0..12                                                                                        | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| ncm-id      | Generate the tech-support file with information from specific NCCs , NCMs, and NCPs.                                                                                                                                                   | 0A, 0B, 1A, 1B                                                                               | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| info-type   | Specifies the type of files to be included ion tech-support info                                                                                                                                                                       | basic - include all textual log files                                                        |               |
|             |                                                                                                                                                                                                                                        | core-dumps - process binary core dump files (not included by default)                        |               |
|             |                                                                                                                                                                                                                                        | journal-files - binary output of Active NCC Base-OS journal files (not included by default). |               |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| before-time | The tech-support file will only include information generated before the specified time.                                                                                                                                               | yyyy-mm-ddThh:mm:ss[.sss]                                                                    | Last 24 hours |
|             | Can be used in combination with "after" to create a range of dates.                                                                                                                                                                    |                                                                                              |               |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| after-time  | The tech-support file will only include information generated after the specified time.                                                                                                                                                | yyyy-mm-ddThh:mm:ss[.sss]                                                                    | Last 24 hours |
|             | Can be used in combination with "before" to create a range of dates.                                                                                                                                                                   |                                                                                              |               |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+

**Example**
::

	gi# request system tech-support MyTechSupportFile
	13:32:00_30-01-2018 System is generating a Tech-support file
	gi#

	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

	gi# request system tech-support MyTechSupportFile include core-dumps
	13:32:00_30-01-2018 System is generating Tech-support file
	gi#
	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

	gi# request system tech-support MyTechSupportFile include basic, core-dumps
	13:32:00_30-01-2018 System is generating Tech-support file
	gi#
	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

	gi# request system tech-support MyTechSupportFile ncc-all
	13:32:00_30-01-2018 System is generating Tech-support file
	gi#
	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

	gi# request system tech-support MyTechSupportFile ncc 0 after 2020-01-02T07:35:00 force
	13:32:00_30-01-2018 System is generating Tech-support file
	gi#
	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

	gi# request system tech-support MyTechSupportFile
	Warning: Previous techsupport files exist. Are you sure you want to erase?  (Yes/No) [No]? Yes
	GI# Tech-support request: Done: /techsupport/ts_MyTechSupportFile_13_35_07_30-01-2018.tar

**Command History**

+---------+---------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                    |
+=========+=================================================================================================================================+
| 16.1    | Command introduced                                                                                                              |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
