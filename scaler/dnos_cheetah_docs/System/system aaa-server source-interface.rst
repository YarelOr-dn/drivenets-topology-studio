system aaa-server source-interface
----------------------------------

**Minimum user role:** operator

An AAA client selects a random interface as the egress interface for AAA messages. The selected interface's IP address is used as source-address in the packets' headers. You can change this behavior by setting a source-interface whose IP address will be used for all AAA messages outgoing to in-band AAA servers. The egress interface will be selected according to the routing table route lookup.

To configure the AAA server's source interface:

**Command syntax: source-interface [interface-name]**

**Command mode:** config

**Hierarchies**

- system aaa-server


**Note**

	- The following configuration can be overrided under the specific server source-interface config, and applies only for the VRF default.

    - If you do not configure an NTP source interface, the system in-band-management source-interface will be used. If you do not have an system in-band-management source-interface configured, NTP messages will not be generated.
	    - Exception: Supported by TACACS Only: in case source-interface isn't configured on any of above, and there is at least 1 interface configured with DHCP enabled that acquired an address and a default route in the “default” VRF context, it will be used for all the outgoing NTP messages.

	- Support Validation that ipv4 or/and IPv6 address must be configured on the interface configuration.

	- 'no source-interface' - remove source-interface configuration

**Parameter table**

+------------------+----------------------------------------------------------------+------------------------------------------------------------------------------------------+--------------------------------------------+
| Parameter        | Description                                                    | Range                                                                                    | Default                                    |
+==================+================================================================+==========================================================================================+============================================+
| source-interface | The source interface whose IP address is used for AAA messages | Any interface in the default VRF with an IPv4/IPv6 address, except GRE tunnel interfaces | system in-band-management source-interface |
+------------------+----------------------------------------------------------------+------------------------------------------------------------------------------------------+--------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# source-interface lo0




**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system-aaa)# no source-interface


**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 11.0    | Command introduced                    |
+---------+---------------------------------------+
| 15.1    | Added support for IPv6 address format |
+---------+---------------------------------------+
