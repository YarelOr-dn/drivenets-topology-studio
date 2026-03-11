No commands
-----------

To distinguish "no" commands from "configure" commands, the help for menu items under the "no" hierarchy begins with the action word: Remove

Example

For the general command: configure no system snmp user <<user_name>> view, the following is the help hierarchy:

Configure Configure mode

no Remove configuration

system Remove system

snmp Remove SNMP

user Remove SNMP user

<text> User name (36 characters)

view Remove system SNMP user view

+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|          | Note:                                                                                                                                                                                                                                                                        |
|          |                                                                                                                                                                                                                                                                              |
|          | All menu items under "no" begin with "Remove".                                                                                                                                                                                                                               |
|          |                                                                                                                                                                                                                                                                              |
|          | Parameters under the "no" hierarchy **do not** begin with "Remove" (<text> denoting User name in the example above).                                                                                                                                                         |
|          |                                                                                                                                                                                                                                                                              |
|          | The help line for "no" is: Remove configuration; for subsequent menu items under the "no" hierarchy, there is no need to repeat the word "configuration". Hence, "Remove system" and not "Remove system configuration". We tried to keep the help line as short as possible. |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
