system in-band-management source-interface
------------------------------------------

**Minimum user role:** operator

The configuration relates to both IPv4 and IPv6 address families. If IPv4 or IPv6 address is not configured for the source interface, the client management applications will not work for the appropriate address-family. Changing the IPv4 or IPv6 address on the selected interface requires that the source-IP address of the client protocol packets be updated immediately.

Set the source interface for all in-band default VRF (VRF-0) management applications (for example, NTP, SNMP, Syslog, and TACACS), using the following command:

**Command syntax: in-band-management source-interface [interface-name]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- If system in-band management interface is not defined (or if it doesn't have an IP address), and the source-interface is not defined for a specific protocol, no packets will be generated for this protocol.

	- As an exception, if the source-interface is defined for specific per-protocol server then the packets will be generated for it.

	- As an exception, if the in-band-management source-interface is defined for specific non-default VRF then the packets will be generated for it.

- The following client management applications are supported:

	- TACACS

	- SNMP trap

	- Syslog

	- IPFIX/Netflow

	- DNS

	- NTP

.. - Any VRF-0 loopback interface may be selected

	- In v11.1 and earlier, only Lo-0 interface is supported

	- Selected interface must include both IPv4 and IPv6 addresses

	   - "no interface ipv4-address / ipv6-address command can be applied to the selected interface

	- Interface cannot be removed if it is selected as source interface for in-band management

	- If selected interface has more than one IP address, default IP address will be used as a a source interface

	- The selected interface refers both to IPv4 and IPv6 addresses

	- If ipv4/ipv6 address is changed on the selected interface, the source-IP address of the client protocol packets must be updated immediately

	- If "system in-band-management interface is not set and source-interface is not set for a specific protocol, no packets will be generated for this protocol"

**Parameter table**

+----------------+---------------------------------------------------+-----------------------------------------------+---------+
| Parameter      | Description                                       | Range                                         | Default |
+================+===================================================+===============================================+=========+
| interface-name | The name of the interface for in-band management. | Any loopback interface in default VRF (VRF-0) | \-      |
+----------------+---------------------------------------------------+-----------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# in-band-management source-interface lo0 
	
	
	
	


**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no in-band-management source-interface

.. **Help line:** configure source-interface for in-band management applications

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 5.1.0   | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 6.0     | Changed ip-version syntax                                      |
|         | Applied new hierarchy                                          |
+---------+----------------------------------------------------------------+
| 11.0    | Added IPv6 support, removed ip-version from the command syntax |
+---------+----------------------------------------------------------------+
| 13.0    | Updated range of interface-name                                |
+---------+----------------------------------------------------------------+

