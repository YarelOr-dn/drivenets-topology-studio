request system restart rollback
-------------------------------

**Minimum user role:** operator

You can generate a file with all the logs, configuration, database files and system output commands that you can save for later use (for example, when opening a customer support case).

After running the command, you will regain full CLI control while the system is generating the tech-support file in the background.

The system can handle only one request to generate a tech-support file at a time. If the system is already creating a tech-support file while you enter another request, an error message will be displayed.

To generate the tech-support file:

**Command syntax: request system restart rollback [rollback-id]**

**Command mode:** operation 

**Note**

- By default, generate tech-support with information from the last 24 hours for rotated logs (end with .1, .2, date, etc.) and always include the latest version of the main logs (logs that are currently being written to) regardless if they were modified in the past 24 hours.

- The Tech-support files are generated on the active NCC node at /techsupport/ Only one file is stored at a time. 

- When you generate a tech-support file, a previous file will be deleted to make room for the new file.

.. - Request system restart performs applicative containers restart across all the system.

	- Applicative containers are Management-engine, Routing-engine, Forwarding-engine and selector.

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| Parameter   | Description                                                                                                                                                                                                                            | Range                                                                                        | Default       |
+=============+========================================================================================================================================================================================================================================+==============================================================================================+===============+
| file-name   | Provide a name for the file. A date suffix is added to the user provided name: _HH:MM:SS_DD-MM-YY.tar                                                                                                                                  | \-                                                                                           | \-            |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------+---------------+
| component   | Include information from the specified DNOS component.                                                                                                                                                                                 | All - generate file with information from all components                                     | All           |
|             |                                                                                                                                                                                                                                        | Datapath - generate file with information from datapath components only                      |               |
|             |                                                                                                                                                                                                                                        | Infra - generate file with information from infrastructure components only                   |               |
|             |                                                                                                                                                                                                                                        | Management - generate file with information from management components only                  |               |
|             |                                                                                                                                                                                                                                        | Routing - generate file with information from routing components only                        |               |
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

	dnRouter(RECOVERY)# request system restart rollback 2
	

**Command History**

+---------+---------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                    |
+=========+=================================================================================================================================+
| 5.1.0   | Command introduced                                                                                                              |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Added forwarder-id option                                                                                                       |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Updated syntax to new architecture                                                                                              |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Added the command to recovery mode, updated the syntax of the operation mode to include type, component, and force              |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
| 11.5    | Added option to include files before and/or after a specific date. Removed the command from recovery mode (was not implemented) |
+---------+---------------------------------------------------------------------------------------------------------------------------------+
| 13.1    | Updated parameter values                                                                                                        |
+---------+---------------------------------------------------------------------------------------------------------------------------------+



