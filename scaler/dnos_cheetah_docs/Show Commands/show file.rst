show file
----------

**Command syntax: show file** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-id] | all} **[file-type] {[ file-name ] \| list }**
**Description:** displays file output according to type of file

By default, display file/s from active ncc. Can set to display file from a specific node in cluster by specifing node type and id. Can set to display files from the entire cluster by using all.


For file types of config, log or traces, file-name can include regex to display all files matching expression.
Output will be printed sequencially according to sorting of matching files name.
User can use pipe commands to filer results of multiple files

**CLI example:**
::

	dnRouter# show file ncc 0 config MyConfigFile
	dnRouter# show file ncc 0 log ldp
	dnRouter# show file ncp 0 log ldp


	dnRouter# show file log list
	| Type |Id | File name                              | Size  | Last modified            |
	|------+---+----------------------------------------+-------+--------------------------|
	| NCC  |0  | ospf                                   | 4.0K  | 12-Jan-2017 22:05:01 UTC |
	| NCC  |0  | ldpd                                   | 4.0K  | 12-Jan-2017 22:05:01 UTC |

	dnRouter# show file all core list

	| Type   | Id   | File name                                                     | Size [Bytes]   | Last modified            |
	|--------+------+---------------------------------------------------------------+----------------+--------------------------|
	| NCC    | 0    | routing_engine/core-snmpd.51866.sig-6.2020-06-03.13-21-16.tar | 720K           | 03-Jun-2020 13:21:00 UTC |
	| NCC    | 0    | routing_engine/core_dumps_info.txt                            | 153            | 03-Jun-2020 13:21:00 UTC |
	| NCP    | 1    | node-manager/core.orm.cf44d119_0fb0_426c_9d10_0409a39faa71.gz | 538K           | 03-Jun-2020 10:55:00 UTC |



	dnRouter# show file log list | include routing_engine/system-events.log display-headers

	| Type   | Id   | File name                                                                                                      | Size [Bytes]   | Last modified            |
	|--------+------+----------------------------------------------------------------------------------------------------------------+----------------+--------------------------|
	| NCC    | 0    | routing_engine/system-events.log                                                                               | 4.1M           | 26-Nov-2020 12:17:00 UTC |
	| NCC    | 0    | routing_engine/system-events.log.1                                                                             | 5M             | 30-Oct-2020 12:01:00 UTC |


	dnRouter# show file log routing_engine/system-events.log* | include WARNING | include RSVP_TUNNEL

	routing_engine/system-events.log.1: local7.warning 2020-10-25T14:49:04.589Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15_IXIA_ISIS_SCALE_38_Devtest_US_R0_R15_GRIDs_178 from 100.12.12.12 to 105.15.91.37, tunnel ID 186, LSP ID 3859, moved on a bypass tunnel
	routing_engine/system-events.log.1: local7.warning 2020-10-25T14:49:04.590Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15_IXIA_ISIS_SCALE_48_Devtest_US_R0_R15_GRIDs_191 from 100.12.12.12 to 105.15.91.47, tunnel ID 199, LSP ID 3858, moved on a bypass tunnel
	routing_engine/system-events.log.1: local7.warning 2020-10-25T14:49:04.591Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15_IXIA_ISIS_SCALE_37_Devtest_US_R0_R15_GRIDs_181 from 100.12.12.12 to 105.15.91.36, tunnel ID 189, LSP ID 3857, moved on a bypass tunnel
	routing_engine/system-events.log.1: local7.warning 2020-10-25T14:49:04.592Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15_IXIA_ISIS_SCALE_35_Devtest_US_R0_R15_GRIDs_170 from 100.12.12.12 to 105.15.91.34, tunnel ID 177, LSP ID 3856, moved on a bypass tunnel
	routing_engine/system-events.log.1: local7.warning 2020-10-25T14:49:04.604Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15_IXIA_ISIS_SCALE_18_Devtest_US_R0_R15_GRIDs_193 from 100.12.12.12 to 105.15.91.17, tunnel ID 201, LSP ID 3855, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T14:14:47.206Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R13-Core_Devtest_US_R0_Default_BFD_58 from 100.12.12.12 to 100.13.13.13, tunnel ID 60, LSP ID 204, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T14:14:47.207Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R13-Core_Devtest_US_R0_Priority_BFD_57 from 100.12.12.12 to 100.13.13.13, tunnel ID 59, LSP ID 203, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T17:04:45.127Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel R12_R15 from 100.12.12.12 to 100.15.15.15, tunnel ID 226, LSP ID 1435, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T17:04:45.241Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R13-Core_Devtest_US_R0_Default_BFD_58 from 100.12.12.12 to 100.13.13.13, tunnel ID 60, LSP ID 1423, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T17:04:45.390Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R15-Core_Devtest_US_R0_Default_BFD_162 from 100.12.12.12 to 100.15.15.15, tunnel ID 169, LSP ID 1425, moved on a bypass tunnel
	routing_engine/system-events.log: local7.warning 2020-11-25T17:04:45.420Z R12-Core RSVP - - - RSVP_TUNNEL_REROUTED:RSVP tunnel auto_tunnel_R12-Core_R18-Core_Devtest_US_R0_Default_BFD_110 from 100.12.12.12 to 100.18.18.18, tunnel ID 114, LSP ID 1424, moved on a bypass tunnel




**Command mode:** operational

**TACACS role:** viewer

**Note:**

-  all option can only be set with list option

-  show file should provide access only to specific folders where the files exist

   -  cannot display specific file from NCM

-  The user should not have access to other folders

-  pressing tab should provide the list of available files in the folder

-  master log file for each process should have alias name without the file extension ".log". i.e "show file ldp" instead "show file ldp.log". This is relevant ONLY to the master file name of each process (not the rotated files)

-  Implementation should be using "ls", using "list" parameter will be implemented internally by "ls -lh" linux command

-  Each file type has a different location:

	-  config - /config/

	-  log - /var/log/dn/

	-  traces - /var/log/dn/traces

	-  core - /core/

	-  tech-support - /techsupport/

	-  certificate - /security/cert/

	-  key - /security/key/ (list only, do not output the file content)

	-  event-policy - /event-manager/event-policy/scripts/

	-  periodic-policy - /event-manager/periodic-policy/scripts/

	-  generic-policy - /event-manager/generic-policy/scripts/

	-  packet-capture - /packet-capture/

	-  integrity-report-retrieves - /core/integrity_report_retrieves

-  file types to show files on NCCs:

	-  config

	-  log

	-  traces - /var/log/dn/traces

	-  core (list only, do not output the file content)

	-  techsupport (list only, do not output the file content)

	-  certificate - /security/cert/

	-  event-policy - /event-manager/event-policy/scripts/

	-  periodic-policy - /event-manager/periodic-policy/scripts/

	-  generic-policy - /event-manager/generic-policy/scripts/

	-  packet-capture - /packet-capture/

	-  integrity-report-retrieves (list only, do not output the file content)

-  file types to show files on NCPs/NCFs:

	-  log

	-  traces - /var/log/dn/traces

	-  core (list only, do not output the file content)

-  file types to show files on NCMs:

	-  log

	-  config

	-  core (list only, do not output the file content)

	-  techsupport (list only, do not output the file content)

core, tech-support and integrity-report-retrieves output aren't shown, presented on the list output. (only by their file name)

**Help line:**

**Parameter table:**

+-----------+----------------------------------------------------+---------------+
| Parameter | Values                                             | Default value |
+===========+====================================================+===============+
| file-type | log / config / core / tech-support                 |               |
|           | / integrity-report-retrieves                       |               |
|           |                                                    |               |
|           | / certificate / event-policy / periodic-policy     |               |
|           | / generic-policy                                   |               |
+-----------+----------------------------------------------------+---------------+
| file-name | Any string except "list". Including sub-directory. |               |
+-----------+----------------------------------------------------+---------------+
| ncc-id    | 0-1                                                |               |
+-----------+----------------------------------------------------+---------------+
| ncp-id    | 0-249                                              |               |
+-----------+----------------------------------------------------+---------------+
| ncf-id    | 0-611                                              |               |
+-----------+----------------------------------------------------+---------------+
| ncm-id    | a0, b0, a1, b1                                     |               |
+-----------+----------------------------------------------------+---------------+