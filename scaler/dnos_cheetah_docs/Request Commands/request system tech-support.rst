request system tech-support
---------------------------

**Minimum user role:** operator

You can generate a file with all the logs, configuration, database files and system output commands that you can save for later use (for example, when opening a customer support case).

After running the command, you will regain full CLI control while the system is generating the tech-support file in the background.

The system can handle only one request to generate a tech-support file at a time. If the system is already creating a tech-support file while you enter another request, an error message will be displayed.

By default, the tech-support file is generated with information from the last 24 hours for rotated logs (end with .1, .2, date, etc.) and always includes the latest version of the main logs (logs that are currently being written to) regardless if they were modified in the past 24 hours.

The Tech-support files are generated on the active NCC node in the /techsupport/ folder. Only one file is stored at a time. When you generate a tech-support file, any previous file is deleted to make room for the new file.

After generating the tech-support file, you can upload it to a location you can access (see "request file upload").

To generate the tech-support file:


**Command syntax: request system tech-support [file-name]** component [component] {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} inclusive after [after-time] before [before-time] password force include {[info-type], [info-type], ...}

**Command mode:** operational

..
	**Internal Note**

	- The tech-support files are generated with user provided filename_HH:MM:SS_DD-MM-YY.tar.gz

	-   - generate tech-support with core files from both NCCs and all NCPs (under /core)

	-  ncp-id - generate tech-support specific NCCs, NCPs and NCMs only.

	-  Only single techsupport request can be handled by DNOS at the same moment. If another request is given while a different tech-support file is currently created, the following message will be displayed "Cannot produce a new techsupport file, another process is already running"

	-  Only single techsupport file can be stored at /techsupport at a given moment. Generation of new techsupport file will require deletion of old file.

	-  [Node name] [node-id] - generate tech-support file with information of a specific node in the cluster.

  - By default, generate tech-support file that covers all cluster nodes

	-  Component - Select DNOS components for which information will be included in tech-support file

	   -  all - Generate tech-support on all components. default behavior

	   -  datapath - Generate tech-support on datapath components only

	   -  infra - Generate tech-support on infra components only

	   -  management - Generate tech-support on management components only

	   -  routing - Generate tech-support on routing components only

	   -  monilogs - Generate tech-support on monilogs only

	-  inclusive - Generate tech-support file including asic commands which may be service affecting

	-  after - Gather information generated after the specified time.

	  - By default, Generate tech-support with information from the last 24 hours for rotated logs (logs ending in .1, .2, .date etc.) and always
	     the latest version for the main logs (logs that are being currently into and do not have a .1, .2, .date etc. suffix),  regardless if they were modified in the last 24 hours or not

	-  before - Gather information generated after the specified time

	  - By default, Generate tech-support with information from the last 24 hours for rotated logs (logs ending in .1, .2, .date etc.) and always
	     the latest version for the main logs (logs that are being currently into and do not have a .1, .2, .date etc. suffix),  regardless if they were modified in the last 24 hours or not

	-  password - generate tech-support with passwords. By default, passwords are removed from the output

	-  force - automatically delete previous techsupport file. by default user is prompt to choose whether to delete previous techsupport file in order to complete techsupport generation or to cancel operation.

	- info-type - specify types of files to be included in tech-support info

		- basic - include all textual log files

		-  core-dumps - prcoesses binary core dump files.

			- By default, core dumps files are not included in the tech-support tar.

		- journal-files - binary output of Active NCC Base-OS journal files, which are the in memory process logs

			- By default, journal files files are not included in the tech-support tar.


**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| Parameter      | Description                                                                                                                                                                                                                                     | Range                                                                                             | Default          |
+================+=================================================================================================================================================================================================================================================+===================================================================================================+==================+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| file-name      | Provide a name for the file. A date suffix is added to the user provided name: _HH:MM:SS_DD-MM-YY.tar.gz                                                                                                                                        | \-                                                                                                | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| component      | Include information from the specified DNOS component.                                                                                                                                                                                          | All - generate file with information from all components                                          | All              |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | Datapath - generate file with information from datapath components only                           |                  |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | Infra - generate file with information from infrastructure components only                        |                  |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | Management - generate file with information from management components only                       |                  |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | Monilogs - generate file with information from monilogs components only                           |                  |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | Routing - generate file with information from routing components only                             |                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| password       | Generates the tech-support file with passwords. By default, passwords are removed from the output.                                                                                                                                              | \-                                                                                                | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| force          | Automatically delete a previous tech-support file. By default, you will be prompted to choose whether to delete a previous tech-support file in order to complete the generation of the tech-support   file, or to cancel the operation.        | \-                                                                                                | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| ncc-id         | Generate the tech-support file with information from the specified NCC only.                                                                                                                                                                    | 0..1                                                                                              | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| ncp-id         | Generate the tech-support file with information from the specified NCP only.                                                                                                                                                                    | 0..47                                                                                             | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| ncf-id         | Generate the tech-support file with information from the specified NCF only.                                                                                                                                                                    | 0..12                                                                                             | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| ncm-id         | Generate the tech-support file with information from specific NCCs , NCMs, and NCPs.                                                                                                                                                            | 0A, 0B, 1A, 1B                                                                                    | \-               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| info-type      | Specifies the type of files to be included ion tech-support info                                                                                                                                                                                | basic - include all textual log files                                                             |  \-              |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | core-dumps - process binary core dump files (not included by default)                             |                  |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                |                                                                                                                                                                                                                                                 | journal-files - binary output of Active NCC Base-OS journal files (not included by default).      |                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| inclusive      | The tech-support file will include information generated for deep interfaces diagnostics for NCP and NCF only.                                                                                                                                  | \-                                                                                                |  \-              |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                | **This option is considered traffic-affecting and requires system restart after completed.**                                                                                                                                                    |                                                                                                   |                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| before-time    | The tech-support file will only include information generated before the specified time.                                                                                                                                                        | yyyy-mm-ddThh:mm:ss[.sss]                                                                         | Last 24 hours    |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                | Can be used in combination with "after" to create a range of dates.                                                                                                                                                                             |                                                                                                   |                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
| after-time     | The tech-support file will only include information generated after the specified time.                                                                                                                                                         | yyyy-mm-ddThh:mm:ss[.sss]                                                                         | Last 24 hours    |
|                |                                                                                                                                                                                                                                                 |                                                                                                   |                  |
|                | Can be used in combination with "before" to create a range of dates.                                                                                                                                                                            |                                                                                                   |                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------+------------------+

**Example**
::

	dnRouter# request system tech-support MyTechSupportFile
	13:32:00_30-01-2018 System is generating Tech-support file
	dnRouter#

	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56


	dnRouter# request system tech-support MyTechSupportFile include core-dumps
	13:32:00_30-01-2018 System is generating Tech-support file
	dnRouter#
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

	dnRouter# request system tech-support MyTechSupportFile include basic, core-dumps
	13:32:00_30-01-2018 System is generating Tech-support file
	dnRouter#
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

	dnRouter# request system tech-support MyTechSupportFile component infra ncc 1
	13:32:00_30-01-2018 System is generating Tech-support file
	dnRouter#
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

	dnRouter# request system tech-support MyTechSupportFile ncc 0 after 2020-01-02T07:35:00 force
	13:32:00_30-01-2018 System is generating Tech-support file
	dnRouter#
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

	dnRouter# request system tech-support MyTechSupportFile component routing
	Warning: Previous techsupport files exist. Are you sure you want to erase?  (Yes/No) [No]?
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

	dnRouter# request system tech-support MyTechSupportFile ncp 1 inclusive
	Warning: This command may be service-affecting, and as such is considered disruptive.
	/** ENSURE THE ELEMENT IS NOT CARRYING TRAFFIC **/
	Please restart the system once it is completed!
	Are you sure you want to proceed? (Yes/No) [No]?
	Tech-support request: Tech-support ts_MyTechSupportFile_13_35_07_30-01-2018.tar successfully generated on 30-Jan-2018 13:57:56

.. **Help line:**

**Command History**

+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
|             |                                                                                                                                      |
| Release     | Modification                                                                                                                         |
+=============+======================================================================================================================================+
| 5.1.0       | Command introduced                                                                                                                   |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 6.0         | Added forwarder-id option                                                                                                            |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 10.0        | Updated syntax to new architecture                                                                                                   |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 11.0        | Added the command to recovery mode, updated the   syntax of the operation mode to include type, component, and force                 |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 11.5        | Added option to include files before and/or after   a specific date. Removed the command from recovery mode (was not implemented)    |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 13.1        | Updated parameter values                                                                                                             |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 18.2        | Added inclusive parameter for deep interfaces diagnostics for single NCP and NCF only                                                |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+
| 18.2        | Added a new component - monilogs. Collects the monilogs from the node                                                                |
+-------------+--------------------------------------------------------------------------------------------------------------------------------------+