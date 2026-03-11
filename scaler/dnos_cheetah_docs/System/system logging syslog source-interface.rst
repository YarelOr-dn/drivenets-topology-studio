system logging syslog source-interface
--------------------------------------

**Minimum user role:** operator

The syslog source-interface defines the source IP address of packets sent to syslog servers in default VRF (VRF-0). If you do not configure a source-interface, the IP of the system in-band-management source-interface will be used. If an in-band-management source-interface is not configured either, then syslog messages will not be directed to the syslog server.

To configure the source-interface:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system logging syslog


**Note**

- If the interface is configured with multiple IP addresses, the primary address will be used.

- Interface cannot be removed if it is selected as source interface for syslog server in default VRF (VRF-0).

.. - source-interface must be set with IP address (IPv4 or/and IPv6), in case both the IP address families are configured on the source interface the IP address will be assigned according to the server's address family

	- no source-interface command sets the source IP address for the syslog message to be according to the "system in-band-management source-interface" CLI command. If no interface was set for "system in-band-management source-interface", syslog messages will not be exported to the syslog server

	- if interface has more than one IP address, the primary address is used

**Parameter table**

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                  | Range                                                      | Default |
+==================+==============================================================================================================================================================+============================================================+=========+
| source-interface | The interface whose IP address will be used as the source IP address for messages sent to remote syslog servers.                                             | Any interface in the default VRF with an IPv4/IPv6 address | \-      |
|                  | In the event that both IP address families are configured on the source-interface, the IP address will be assigned according to the server's address family. |                                                            |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# source-interface bundle-1 
	
	

**Removing Configuration**

To remove the default source-interface used by servers in default VRF (VRF-0):
::

	dnRouter(cfg-system-logging-syslog)# no source-interface

.. **Help line:** Configure source-interface for syslog server

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 11.0    | Command introduced                    |
+---------+---------------------------------------+
| 15.1    | Added support for IPv6 address family |
+---------+---------------------------------------+


