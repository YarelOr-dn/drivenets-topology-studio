system logging syslog server
----------------------------

**Minimum user role:** operator

To send logs to a remote syslog server, configure the remote syslog server and enter its configuration mode. You can configure up to 10 remote servers. The server address can be IPv4/IPv6.

**Command syntax: server [server-address | server-hostname] vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system logging syslog


**Note**

- Notice the change in prompt

- The syslog exporting is supported for mgmt0 (out-of-band) and all in-band VRFs.

- VRF cannot be removed if it is used by a syslog server.

.. - "no server" command removes all the syslog-servers

	- "no server [ip vrf]" command removes specific syslog-servers

	- server address can be either IPv4/IPv6 address or fully/partially qualified domain name

	- syslog exporting is done per vrf, "default" vrf represents in-band management and "mgmt0" vrf represents out-of-band management channel.

	- syslog source address type will be set according to the destination server IP address type.

	- up to 10 syslog servers are supported

**Parameter table**

+-----------------+----------------------------------------------------------------------------------------------+---------------------------+---------+
| Parameter       | Description                                                                                  | Range                     | Default |
+=================+==============================================================================================+===========================+=========+
| server-address  | The IPv4/IPv6 address of the remote server                                                   | A.B.C.D                   | \-      |
|                 |                                                                                              | xx:xx::xx:xx              |         |
+-----------------+----------------------------------------------------------------------------------------------+---------------------------+---------+
| vrf-name        | Defines whether syslog server management is in-band (default VRF) or out-of-band (mgmt0 VRF) | default - in-band         | \-      |
|                 |                                                                                              | mgmt0 - out-of-band       |         |
|                 |                                                                                              | (name of non-default VRF) |         |
+-----------------+----------------------------------------------------------------------------------------------+---------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog-server)#
	dnRouter(cfg-system-logging-syslog)# server 2001:ab12::1 vrf mgmt0
	dnRouter(system-logging-syslog-server)#
	dnRouter(cfg-system-logging-syslog)# server 2.3.4.5 vrf my_vrf
	dnRouter(system-logging-syslog-server)#



**Removing Configuration**

To remove a syslog server:
::

	dnRouter(system-logging-syslog)# no server 1.2.3.4 vrf default
	dnRouter(system-logging-syslog)#
	dnRouter(system-logging-syslog)# no server 2001:ab12::1 vrf default
	dnRouter(system-logging-syslog)#
 	dnRouter(system-logging-syslog)# no server 2.3.4.5 vrf my_vrf
 	dnRouter(system-logging-syslog)#

.. **Help line:** Configure system logging syslog server

**Command History**

+---------+-------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                          |
+=========+=======================================================================================================+
| 5.1.0   | Command introduced                                                                                    |
+---------+-------------------------------------------------------------------------------------------------------+
| 6.0     | Applied new hierarchy                                                                                 |
+---------+-------------------------------------------------------------------------------------------------------+
| 10.0    | Applied new hierarchy                                                                                 |
+---------+-------------------------------------------------------------------------------------------------------+
| 11.0    | Moved from logging hierarchy to syslog hierarchy. Changed the syntax from "syslog-server" to "server" |
+---------+-------------------------------------------------------------------------------------------------------+
| 11.4    | Added option to configure a server using its hostname                                                 |
+---------+-------------------------------------------------------------------------------------------------------+
| 13.1    | Added support for syslog-server out-of-band management in addition to in-band management using VRF    |
+---------+-------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for IPv6 address format                                                                 |
+---------+-------------------------------------------------------------------------------------------------------+
| 18.1    | Removed the option to configure a server using its hostname                                           |
+---------+-------------------------------------------------------------------------------------------------------+
