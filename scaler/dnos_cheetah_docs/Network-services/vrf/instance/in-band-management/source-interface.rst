network-services vrf instance in-band-management source-interface
-----------------------------------------------------------------

**Minimum user role:** operator

To configure the source-interface for in-band management applications over the non-default VRF (for example: syslog, snmp trap-client, dns-client, tacacs-client, radius-client, ntp-client):

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance in-band-management

**Note**
- Any loopback interface associated with the VRF can be selected.
- The source-interface for non-default vrf should behave as following:
- If explicitly specified under non-default VRF for configured client-side management protocol, then it will be used for all the outgoing packets through that non-default VRF context.
- Other in-band-management source-interface that is specified under the same VRF as the management protocol will be used for the management protocol.
- If in-band-management source interface is not set and source-interface is not set for a specific management protocol, no packets will be generated for this protocol.
- If the selected interface has more than one IP address, the global IP address will be used as a source interface.
- The selected interface refers both to IPv4 and IPv6 addresses.
- If ipv4/ipv6 address is changed on the selected interface, the source-IP address of the client protocol packets must be updated immediately.

**Parameter table**

+------------------+-----------------------------------------------------------------------+-------------------------------------------------+---------+
| Parameter        | Description                                                           | Range                                           | Default |
+==================+=======================================================================+=================================================+=========+
| source-interface | source interface for all non-default in-band management applications. | loopback interfaces assigned to non-default VRF | \-      |
+------------------+-----------------------------------------------------------------------+-------------------------------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance my_vrf
    dnRouter(cfg-netsrv-vrf)# in-band-management
    dnRouter(cfg-vrf-inband-mgmt)# source-interface lo4

    dnRouter(cfg-vrf-inband-mgmt)# no source-interface


**Removing Configuration**

To remove services for non-default VRFs:
::

    no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
