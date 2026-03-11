network-services vrf instance interface
---------------------------------------

**Minimum user role:** operator

To attach an interface to a VRF (Virtual Route Forwarding) instance:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance

**Note**

- Multiple interfaces can be attached to a VRF instance.

- By default, all network interfaces are attached to the default VRF.

- A network interface can only be attached to a single VRF instance (default/user-configured non-default VRF), but not to any of the management VRFs.

- When an interface is deleted from the VRF, the interface is automatically reattached to the default VRF.

- Validation: a user cannot attach a non-existing interface or interfaces already attached to non-default VRFs without unattaching them first.

- Validation: if the user removes an attached network interface from a VRF instance, then as long as there is no overlap of IP addresses in the default VRF, the specified interfaces will be removed and reattached to the default VRF with its existing configuration. Otherwise, the commit will fail with the message 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv4-address <ipv4-address> overlaps with <ipv4-address> on interface <interface-name>'; or 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv6-address <ipv6-address> overlaps with <ipv6-address> on interface <interface-name>', as applicable.

- Validation: if the user deletes a VRF instance while interfaces are attached to it, then as long as there is no overlap of IP addresses in the default VRF, then all attached interfaces will be removed and reattached to the default VRF with their existing configuration. Otherwise, the commit will fail with the message 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv4-address <ipv4-address> overlaps with <ipv4-address> on interface <interface-name>'; or 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv6-address <ipv6-address> overlaps with <ipv6-address> on interface <interface-name>', as applicable.

- Validation: when a user attaches an interface to a different vrf (including default vrf), the system will preserve the interface with all of its configuration (i.e admin state, ipv4/6 parameters, static arp/ndp entries, etc). If there is an overlapping of the same IP addresses in the target vrf, the command will fail with explanation 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv4-address <ipv4-address> overlaps with <ipv4-address> on interface <interface-name>'; or 'Error: failed to set interface <interface-name> to vrf <vrf-name>. interface ipv6-address <ipv6-address> overlaps with <ipv6-address> on interface <interface-name>', as applicable.

- Validation: VRF cannot be changed for an unnumbered interface or source-interface (donor interface).

- If a sub-interface is moved between VRFs, then it will momentarily go down and then immediately go back up while its parent interface and other sub-interfaces will remain up; However, when a parent interface is moved between VRFs, then it will momentarily go down along with all of its sub-interfaces before going back up.

**Parameter table**

+----------------+-------------------------------------------------+-------------------------------------------+---------+
| Parameter      | Description                                     | Range                                     | Default |
+================+=================================================+===========================================+=========+
| interface-name | References the configured name of the interface | | geX-<f>/<n>/<p>                         | \-      |
|                |                                                 | |                                         |         |
|                |                                                 | | geX-<f>/<n>/<p>.<sub-interface-id>      |         |
|                |                                                 | |                                         |         |
|                |                                                 | | bundle-<bundle-id>                      |         |
|                |                                                 | |                                         |         |
|                |                                                 | | bundle-<bundle-id>.<sub-interface-id>   |         |
|                |                                                 | |                                         |         |
|                |                                                 | | lo<lo-interface-id>                     |         |
+----------------+-------------------------------------------------+-------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# interface bundle-1
    dnRouter(cfg-netsrv-vrf-inst)# interface ge100-1/1/1.10

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_3
    dnRouter(cfg-netsrv-vrf-inst)# interface ge100-1/1/1.20


**Removing Configuration**

To remove the attachment of a network interface from a VRF instance:
::

    dnRouter(cfg-netsrv-vrf-inst)# no interface ge100-1/1/1.10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
