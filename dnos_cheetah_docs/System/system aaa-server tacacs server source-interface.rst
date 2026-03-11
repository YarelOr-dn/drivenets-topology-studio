system aaa-server tacacs server priority address source-interface
-----------------------------------------------------------------

**Minimum user role:** operator

An AAA client selects a random interface as the source-interface for AAA messages per server. The selected interface's IP address is used as source-address in the packets' headers. You can change this behavior by setting a source-interface whose IP address will be used for all AAA messages outgoing to in-band AAA servers. The egress interface will be selected according to the routing table route lookup.

To configure the AAA server's source interface:


**Command syntax: source-interface [interface-name]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
- The source-interface configuration, by default used global configuration for source interface under "system inband source-interface" for VRF default and "network-services vrf instance in-band-management source-interface" for non-default in-band management VRF.
- If the source-interface under the TACACS server is specified it will override the global source-interface config for that server.
- Validation: the source-interface is associated with the same VRF as the TACACS server, otherwise the commit fails validation.
- Validation that ip address must be configured on the interface configuration.
- The source-interface must be configured with the same address type as the remote SNMP server otherwise the TACACS packets won't be sent.
- Only an mgmt0 source-interface can be supported for mgmt0 VRF and it is the default value.
- 'no source-interface' - remove source-interface configuration, if the global source-inteface is configured it will be used.


**Parameter table**

+----------------+----------------------------------------------------------------------------------+-------------------------------------------------------+---------+
| Parameter      | Description                                                                      | Range                                                 | Default |
+================+==================================================================================+=======================================================+=========+
| interface-name | The name of the interface whose source IP address will be used for all TACACS    | | A configured interface:                             | \-      |
|                | packets, towards the current server.                                             | | ge<interface speed>-<A>/<B>/<C>                     |         |
|                | This interface must be configured with an IPv4 or/and IPv6 address.              | | e<interface speed>-<A>/<B>/<C>.<sub-interface id>   |         |
|                | The source-interface must be configured with the same address type as the remote | | bundle-<bundle id>                                  |         |
|                | snmp server, otherwise the TACACS packets won't be sent.                         | | bundle-<bundle id>.<sub-interface id>               |         |
|                |                                                                                  | | lo<lo-interface id>. irb<irb-interface id>          |         |
+----------------+----------------------------------------------------------------------------------+-------------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# source-interface lo1


**Removing Configuration**

To delete the source-interface configuration:
::

    dnRouter(cfg-aaa-tacacs-server)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
