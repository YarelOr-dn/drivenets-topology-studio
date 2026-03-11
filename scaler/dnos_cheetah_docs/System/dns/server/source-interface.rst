system dns server priority ip-address source-interface
------------------------------------------------------

**Minimum user role:** operator

By default, packets sent to a remote DNS server use the IP address of the configured system in-band-management source-interface in the DNS messages. To change the source IP address:

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system dns server priority ip-address

**Note**
- The source-interface configuration, by default used global configuration for source interface under "system inband source-interface" for VRF default and "network-services vrf instance in-band-management source-interface" for non-default in-band management VRF.
- If the source-interface under the TACACS server is specified it will override the global source-interface config for that server.
- Validation: the source-interface is associated with the same VRF as the TACACS server, otherwise the commit will fail the validation.

- Validation: the IP address must be configured on the interface configuration.

- The source-interface must be configured with the same address type as the remote DNS server otherwise the DNS packets won't be sent.

-  Only an mgmt0 source-interface can be supported for mgmt0 VRF and it is the default value.

- 'no source-interface' - remove source-interface configuration, if the global source-inteface is configured it will be used.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+----------------------------------------------------------+---------+
| Parameter        | Description                                                                      | Range                                                    | Default |
+==================+==================================================================================+==========================================================+=========+
| source-interface | The name of the interface whose source IP address will be used for all DNS       | | A configured interface:                                | \-      |
|                  | packets, towards the current server.                                             | |                                                        |         |
|                  | This interface must be configured with an IPv4 or/and IPv6 address.              | |   ge<interface speed>-<A>/<B>/<C>                      |         |
|                  | The source-interface must be configured with the same address type as the remote | |                                                        |         |
|                  | DNS server, otherwise the DNS packets won't be sent.                             | |   ge<interface speed>-<A>/<B>/<C>.<sub-interface id>   |         |
|                  |                                                                                  | |                                                        |         |
|                  |                                                                                  | |   bundle-<bundle id>                                   |         |
|                  |                                                                                  | |                                                        |         |
|                  |                                                                                  | |   bundle-<bundle id>.<sub-interface id>                |         |
|                  |                                                                                  | |                                                        |         |
|                  |                                                                                  | |   lo<lo-interface id>. irb<irb-interface id>           |         |
+------------------+----------------------------------------------------------------------------------+----------------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# server priority 1 ip-address 12.127.17.83 vrf default
    dnRouter(cfg-system-dns-server)# source-interface bundle-2


**Removing Configuration**

To revert source-interface to default:
::

    dnRouter(cfg-system-dns)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
