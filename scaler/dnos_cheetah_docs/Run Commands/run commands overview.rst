Run Commands Overview
---------------------
Run commands enable to run general system running commands, such as monitoring system processes, counters, ping, etc.

::
	dnRouter# run [argument]


**Command mode:** operation

where

[argument] - the specific run command that you want to perform

The following are the available arguments:

+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| Argument                   | Description                                                                                                | Reference                             |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| monitor interface counters | Enables to monitor interface counters. The displayed information is refreshed every 1 second.              | run monitor interfaces counters       |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| ping                       | Enables to check the accessibility of a destination interface.                                             | run ping                              |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| traceroute                 | Enables to display the route that packets take to the specified destination address.                       | run traceroute                        |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| ping mpls rsvp             | Enables to check the accessibility of an RSVP tunnel                                                       | run ping mpls rsvp                    |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| ping mpls bgp-lu           | Enables to check the accessibility of a BGP-LU LSP                                                         | run ping mpls bgp-lu                  |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| traceroute mpls rsvp       | Enables to display the route that packets take along an RSVP tunnel                                        | run traceroute mpls rsvp              |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| traceroute mpls bgp-lu     | Enables to display the route that packets take along a BGP-LU LSP                                          | run traceroute mpls bgp-lu            |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| ssh                        | Enables to make a secure connection to another device.                                                     | run ssh                               |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| system datetime            | Manually set the system clock.                                                                             | set system datetime                   |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| timestamp                  | Turn on CLI timestamp.                                                                                     | set cli-timestamp                     |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| system snmp walk           | Retrieve and display the SNMP object values that are associated with the requested object identifier (oid) | run system snmp walk                  |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| system snmp get            | Retrieve and display one or more SNMP object values                                                        | run system snmp get                   |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| system snmp getnext        | Retrieve and display the next SNMP object values                                                           | run system snmp getnext               |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+
| run start shell            | Access the NCC shell                                                                                       | run start shell                       |
+----------------------------+------------------------------------------------------------------------------------------------------------+---------------------------------------+

