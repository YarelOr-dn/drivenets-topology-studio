system dns source-interface
---------------------------

**Minimum user role:** operator

By default, packets sent to a remote DNS server use the IP address of the configured system in-band-management source-interface in the DNS messages. To change the source IP address:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system dns

**Note**

- If you do not configure a DNS source interface, the system in-band-management source-interface will be used. If you do not have an system in-band-management source-interface configured, DNS messages will not be generated.

- The source address type will be set according to the IP address of the destination server.

**Parameter table**

+------------------+----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+
| Parameter        | Description                                                    | Range                                                                            | Default                                    |
+==================+================================================================+==================================================================================+============================================+
| source-interface | The source interface whose IP address is used for DNS messages | Any interface in the default VRF with an IPv4/IPv6 address, except GRE tunnel    | system in-band-management source-interface |
|                  |                                                                | interfaces                                                                       |                                            |
+------------------+----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# source-interface bundle-1


**Removing Configuration**

To revert source-interface to default:
::

    dnRouter(cfg-system-dns)# no source-interface

**Command History**

+---------+---------------------------------------+
| Release | Modification                          |
+=========+=======================================+
| 11.1    | Command introduced                    |
+---------+---------------------------------------+
| 15.1    | Added support for IPv6 address format |
+---------+---------------------------------------+
