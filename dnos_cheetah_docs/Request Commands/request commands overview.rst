Request Commands Overview
-------------------------
Request commands enable to make system-level requests. To enter a system level request, use one of the following command syntax:

::

	dnRouter# request system [argument]

	or

	dnRouter# request file-[operation]

**Command mode:** operation

where

request system - the command that you enter to request a system-level action

The following are the available system arguments:

+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| Argument                                 | Description                                                                                       | Reference                                             |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| restart                                  | Restarts the system                                                                               | request system restart                                |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| restart process                          | Restarts the specified process                                                                    | request system process restart                        |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| restart recovery                         | Restarts the system and enters recovery mode                                                      | request system restart recovery                       |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| restart factory-default                  | Restarts the system and deletes the database. Applicable to recovery mode only.                   | request system restart factory-default                |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| tech-support                             | Generates a tech-support file with logs, configuration, database files and system output commands | request system tech-support                           |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| traffic-engineering pcep activate-server | Reconnects idle PCEs                                                                              | request mpls traffic-engineering pcep activate-server |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| traffic-engineering pcep delegate peer   | Manually delegate all tunnels to a specific PCE                                                   | request mpls traffic-engineering pcep delegate peer   |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+
| traffic-engineering pcep revoke          | Manually revoke tunnel delegation                                                                 | request mpls traffic-engineering pcep revoke          |
+------------------------------------------+---------------------------------------------------------------------------------------------------+-------------------------------------------------------+

The following are the operations that you can perform on a file:

+-------------+----------------------------------------------------------+-----------------------+
| Operation   | Description                                              | Reference             |
+-------------+----------------------------------------------------------+-----------------------+
| upload      | Copy file from the DN cloud server to an external server | request file upload   |
+-------------+----------------------------------------------------------+-----------------------+
| download    | Copy file to the DN cloud server from an external server | request file download |
+-------------+----------------------------------------------------------+-----------------------+
| file-delete | Delete a file from the DN cloud server                   | request file delete   |
+-------------+----------------------------------------------------------+-----------------------+

The following paragraphs describe each system request.