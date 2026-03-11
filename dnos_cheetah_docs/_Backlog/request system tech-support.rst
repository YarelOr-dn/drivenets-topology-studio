request system tech-support 
----------------------------

**Command syntax: request system tech-support [file-name]** type [type] component [component] password force {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id]} history [time] severity [severity]

**Description:** generate system tech-support file

-  type - set tech-support type to control which information is added to tech-support file.

   -  normal - generate tech-support with process trace information but without core files. default behavior

   -  minimal - generate tech-support with only the most recent process trace information.

   -  extended - generate tech-support with core files. by default, exclude core files from tech-support file

-  [Node name] [node-id] - generate tech-support file with information of a specific node in the cluster. By default, generate tech-support file that covers all nodes. **- supported in v11.1**

-  Component - Select DNOS components for which information will be included in tech-support file

   -  all - Generate tech-support on all components. default behavior

   -  datapath - Generate tech-support on datapath components only

   -  infra - Generate tech-support on infra components only

   -  management - Generate tech-support on management components only

   -  routing - Generate tech-support on routing components only

-  history - the maximum amount of log history, in minutes, to include in the tech-support file. by default, no history time limitation (history 0) **- supported in v11.1**

-  severity - specify log severity level to include in tech-support file, include matching severity and higher. default severity level - debug **- supported in v11.1**

-  password - generate tech-support with passwords. By default, passwords are removed from the output

-  force - automaticly delete previous techsupport file. by default user is prompt to choose whether to delete previous techsupport file in order to complete techsupport generation or to cancel operation.

**CLI example:**
::

	dnRouter# request system tech-support MyTechSupportFile
	13:32:00_30-01-2017 System is generating Tech-support file
	dnRouter#
	
	Tech-support request: Tech-support successfully generated on MyTechSupportFile_13_35_07_30-01-2018.tar.gz
	
	
	dnRouter# request system tech-support MyTechSupportExtendedFile type extended password force
	13:32:00_30-01-2017 System is generating Tech-support file
	dnRouter#
	Tech-support request: Tech-support successfully generated on MyTechSupportFile_13_35_07_30-01-2018.tar.gz
	
	
	dnRouter# request system tech-support MyTechSupportExtendedFile type minimal component routing
	Warning: Previous techsupport files exist. Are you sure you want to erase?  (Yes/No) [No]?
	
	
	dnRouter# request system tech-support MyTechSupportExtendedFile breif ncc 2 history 10 force
	15:32:00_30-01-2017 System is generating Tech-support file
	dnRouter#
	
	Tech-support request: Tech-support successfully generated on MyTechSupportFile_13_35_07_30-01-2018.tar.gz
	
	
**Command mode:** operational

**TACACS role:** operator

**Note:**

-  User gets back cli prompt after invoking "request system tech-support" user have full CLI support while techsupport is being generated in the background.

-  Tech-support files are generated on active NCC node at /techsupport/

-  tech-support files are generated with user provided filename_HH:MM:SS_DD-MM-YY.tar.gz

-  extended - generate tech-support with core files from both NCCs and all NCPs (under /core)

-  ncp-id - generate tech-support from NCCs and specific NCP only.

-  Only single techsupport request can be handled by DNOS at the same moment. If another request is given while a different tech-support file is currently created, the following message will be displayed "Cannot produce a new techsuppot file, another process is already running"

-  Only single techsupport file can be stored at /techsupport at a given moment. Generation of new techsupport file will require deletion of old file.

**Help line:**

**Parameter table:**

+-----------+-----------------------------------------------------------------+---------------+---------------+
| Parameter | Values                                                          | Default value | Comments      |
+===========+=================================================================+===============+===============+
| file-name | string                                                          |               |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| type      | regular, minimal, extended                                      | regular       |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| component | all, datapath, infra, management, routing                       | all           |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| ncc-id    | 0-1                                                             |               |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| ncp-id    | 0-47                                                            |               |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| ncf-id    | 0-12                                                            |               |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| ncm-id    | a0, b0, a1, b1                                                  |               |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| history   | 0-65535                                                         | 0             | minutes       |
|           |                                                                 |               |               |
|           |                                                                 |               | 0 - unlimited |
+-----------+-----------------------------------------------------------------+---------------+---------------+
| severity  | emergency, criticial, error, warning, notification, info, debug | debug         |               |
+-----------+-----------------------------------------------------------------+---------------+---------------+
