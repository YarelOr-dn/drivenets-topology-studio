system ntp source-interface
--------------------------------------

**Minimum user role:** operator

By default, packets sent to a remote NTP server use the IP address of the configured system in-band-management source-interface in the NTP messages. To change the source IP address:

**Command syntax: source-interface [source-interface]**

**Command mode:** configuration

**Hierarchies**

- system ntp


**Note**

- If you do not configure an NTP source interface, the system in-band-management source-interface will be used. If you do not have an system in-band-management source-interface configured, NTP messages will not be generated.

- If the selected interface has multiple IP addresses, the primary address is used.

.. - no source-interface command sets the source IP address for the ntp message to be according to the "system in-band-management source-interface" CLI command. If no interface was set for "system in-band-management source-interface", ntp messages will not be generated.

	- if interface has more than one IP address, the primary address is used

**Parameter table**

+------------------+----------------------------------------------------------------+-------------------------------------------------------------------------------------+--------------------------------------------+
| Parameter        | Description                                                    | Range                                                                               | Default                                    |
+==================+================================================================+=====================================================================================+============================================+
| source-interface | The source interface whose IP address is used for NTP messages | Any interface in the default VRF with an IPv4 address, except GRE tunnel interfaces | system in-band-management source-interface |
+------------------+----------------------------------------------------------------+-------------------------------------------------------------------------------------+--------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ntp
	dnRouter(cfg-system-ntp)# source-interface bundle-1 
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ntp)# no source-interface

.. **Help line:** Configure source-interface for syslog server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+


