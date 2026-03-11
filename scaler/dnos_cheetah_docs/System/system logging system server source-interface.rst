system logging syslog server source-interface
---------------------------------------------

**Minimum user role:** operator

The selected source-interface defines the source IP address of packets sent to syslog servers in corresponding server VRF.

When the source-interface is *not* configured, depending on server VRF, the following rules apply:

- when server VRF is `mgmt0` then the IP address of `mgmt0` interface will be used
- when server VRF is `default` then:
    - if `system logging syslog source-interface` is configured, the IP address of that interface will be used
    - otherwise if `system in-band-management source-interface` is configured, then the IP address of that interface will be used
    - otherwise syslog messages will not be sent to the syslog server
- when server VRF is not `mgmt0` or `default` then:
    - if `network-services vrf instance in-band-management source-interface` is configured, then the IP address of that interface will be used
    - otherwise syslog messages will not be sent to the syslog server

To configure the source-interface:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system logging syslog server


**Note**

- If the interface is configured with multiple IP addresses, the primary address will be used.

- Interface selected as source-interface for syslog server in any VRF cannot be removed.

**Parameter table**

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+---------+
| Parameter        | Description                                                                                                                                                  | Range                                  | Default |
+==================+==============================================================================================================================================================+========================================+=========+
| source-interface | The interface whose IP address will be used as the source IP address for messages sent to remote syslog servers.                                             | Any interface in the corresponding VRF | \-      |
|                  | In the event that both IP address families are configured on the source-interface, the IP address will be assigned according to the server's address family. |                                        |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# server 1.2.3.4 vrf my_vrf
	dnRouter(cfg-logging-syslog-server)# source-interface ge100-0/0/1


**Removing Configuration**

To delete the source-interface configuration of this syslog server and use the defaults provided by: network-services, system logging syslog or system in-band-management (depending on server VRF):
::

	dnRouter(cfg-logging-syslog-server)# no source-interface

.. **Help line:** Configure source-interface for syslog server

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 19.1    | Command introduced                    |
+---------+---------------------------------------+

