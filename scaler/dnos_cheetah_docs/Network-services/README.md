# DNOS Network Services Configuration Reference

This document contains the complete DNOS CLI network services configuration syntax:
- EVPN-VPWS-FXC (Flexible Cross-Connect)
- VRF (Virtual Routing and Forwarding / L3VPN)
- EVPN (MAC-VRF / EVI)
- VPWS (Point-to-Point)
- Bridge-Domain
- Multihoming

---

## network-services
```rst
network-services
----------------

**Minimum user role:** operator

Enter the network-services configuration hierarchy.

**Command syntax: network-services**

**Command mode:** config

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)#


**Removing Configuration**

To remove services for non-default VRFs:
::

    no network-services

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

# EVPN-VPWS-FXC

## counters
```rst
network-services evpn-vpws-fxc counters
---------------------------------------

**Minimum user role:** operator

Define whether counters should be allocated for the EVPN-VPWS-FXC instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# counters
    dnRouter(cfg-netsrv-evpn-vpws-fxc-counters)


**Removing Configuration**

To remove the global evpn-vpws-fxc services counter configuration, restoring to their default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## service-counters
```rst
network-services evpn-vpws-fxc counters service-counters
--------------------------------------------------------

**Minimum user role:** operator

Service-counters disabled is the default setting for EVPN-VPWS-FXC services.
By disabling this knob, service-counters will be disabled for all EVPN-VPWS-FXC instances that do not have a per-instance configuration.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc counters

**Parameter table**

+------------------+--------------------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                                    | Range        | Default  |
+==================+================================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for EVPN-VPWS-FXC services | | enabled    | disabled |
|                  |                                                                                | | disabled   |          |
+------------------+--------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# counters
    dnRouter(cfg-netsrv-evpn-vpws-fxc-counters) service-counters enabled


**Removing Configuration**

To revert the service-counters configuration to its default of disabled
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## evpn-vpws-fxc
```rst
network-services evpn-vpws-fxc
------------------------------

**Minimum user role:** operator

EVPN-VPWS-FXC (Ethernet Virtual Private Network Flexible Cross-connect) is a point-to-point layer 2 VPN service that connects one or more                                                                                                                                                                                                                                                  layer 2 interface(s) of
ACs of a PE device with one or more layer 2 interface(s) of another PE device, across the layer 3 core MPLS network. The EVPN service uses
an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN-VPWS-FXC service configuration mode:

**Command syntax: evpn-vpws-fxc**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws-fxc
    dnRouter(cfg-network-services-evpn-vpws-fxc)#


**Removing Configuration**

To remove all EVPN VPWS FXC services:
::

    dnRouter(cfg-network-services)# no evpn-vpws-fxc

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
network-services evpn-vpws-fxc instance admin-state
---------------------------------------------------

**Minimum user role:** operator

Define the EVPN-VPWS-FXC service instance admin-state. By default the admin-state is enabled.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-------------+------------------------------------+--------------+---------+
| Parameter   | Description                        | Range        | Default |
+=============+====================================+==============+=========+
| admin-state | evpn-vpws-fxc instance admin-state | | enabled    | enabled |
|             |                                    | | disabled   |         |
+-------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# admin-state disabled
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#


**Removing Configuration**

To revert the admin-state to its default: enabled
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## description
```rst
network-services evpn-vpws-fxc instance description
---------------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN-VPWS-FXC:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-------------+---------------------------+------------------+---------+
| Parameter   | Description               | Range            | Default |
+=============+===========================+==================+=========+
| description | evpn-vpws-fxc description | | string         | \-      |
|             |                           | | length 1-255   |         |
+-------------+---------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# description "my evpn-vpws-fxc service"
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)#


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## fxc-mode
```rst
network-services evpn-vpws-fxc instance fxc-mode
------------------------------------------------

**Minimum user role:** operator

The EVPN-VPWS Flexible Cross-connect Service has two modes of operation but currently vlan-aware is the available option.

**Command syntax: fxc-mode [fxc-mode]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Parameter table**

+-----------+------------------------------------------+------------+------------+
| Parameter | Description                              | Range      | Default    |
+===========+==========================================+============+============+
| fxc-mode  | Define whether the service is vlan-aware | vlan-aware | vlan-aware |
+-----------+------------------------------------------+------------+------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-evpn-vpws-fxc-inst)# fxc-mode vlan-aware


**Removing Configuration**

To revert the fxc-mode to its default
::

    dnRouter(cfg-evpn-vpws-fxc-inst)# no fxc-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services evpn-vpws-fxc instance
---------------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN-VPWS-FXC service instance.

**Command syntax: instance [evpn-vpws-fxc-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Note**

- The EVPN-VPWS-FXC service must use a unique name.

**Parameter table**

+--------------------+----------------------------------------------------------------------------+------------------+---------+
| Parameter          | Description                                                                | Range            | Default |
+====================+============================================================================+==================+=========+
| evpn-vpws-fxc-name | The name of the evpn-vpws-fxc -- used to address the evpn-vpws-fxc service | | string         | \-      |
|                    |                                                                            | | length 1-255   |         |
+--------------------+----------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-fxc-evpn-vpws-fxc1)#


**Removing Configuration**

To revert the specified EVPN-VPWS-FXC service to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# no instance evpn-vpws-fxc1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## l2-mtu
```rst
network-services evpn-vpws-fxc instance l2-mtu
----------------------------------------------

**Minimum user role:** operator

Configure the MTU value of this instance to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used, no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | \-      |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## l2-mtu
```rst
network-services evpn-vpws-fxc l2-mtu
-------------------------------------

**Minimum user role:** operator

Configure the default (can be modified per instance) MTU value to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | 0       |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws-fxc
    dnRouter(cfg-network-services-evpn-vpws-fxc)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws-fxc)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws-fxc)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

## transport-protocol
```rst
network-services evpn-vpws-fxc transport-protocol
-------------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS.

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-fxc-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn-vpws-fxc)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
```

# VRF

## description
```rst
network-services vrf instance description
-----------------------------------------

**Minimum user role:** operator

To set a description for the VRF instance:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance

**Note**

- Legal string length is 1-255 characters.

**Parameter table**

+-------------+-----------------+------------------+---------+
| Parameter   | Description     | Range            | Default |
+=============+=================+==================+=========+
| description | vrf description | | string         | \-      |
|             |                 | | length 1-255   |         |
+-------------+-----------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)# description MyDescription-vrf_1

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_2
    dnRouter(cfg-netsrv-vrf-inst)# description My description vrf-2


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-netsrv-vrf-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services vrf instance
-----------------------------

**Minimum user role:** operator

To configure a VRF instance:

**Command syntax: instance [vrf-name]**

**Command mode:** config

**Hierarchies**

- network-services vrf

**Note**

- The legal string length is 1..255 characters.

- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\

- 'no' command deletes the vrf instance and the protocols hierarchy dependencies under the VRF instance. Management protocols, services and other dependencies that rely on the VRF instance or its associated interfaces must be deleted explicitly before deleting the VRF instance.

- By default, the device is configured with the following default VRF instances: 'default', 'mgmt0', 'mgmt-ncc-0' and 'mgmt-ncc-1'. User cannot configure or delete a VRF with these reserved name or with the name 'all'.

- By default, all network interfaces on the device are attached to 'default' VRF.

**Parameter table**

+-----------+------------------------------------------------+------------------+---------+
| Parameter | Description                                    | Range            | Default |
+===========+================================================+==================+=========+
| vrf-name  | The name of the vrf -- used to address the vrf | | string         | \-      |
|           |                                                | | length 1-255   |         |
+-----------+------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf instance customer_vrf_1
    dnRouter(cfg-netsrv-vrf-inst)#


**Removing Configuration**

To remove the specified VRF instance:
::

    dnRouter(cfg-netsrv-vrf)# no instance customer_vrf_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## interface
```rst
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

+----------------+-------------------------------------------------+----------------------------------------------+---------+
| Parameter      | Description                                     | Range                                        | Default |
+================+=================================================+==============================================+=========+
| interface-name | References the configured name of the interface | | geX-<f>/<n>/<p>                            | \-      |
|                |                                                 | |                                            |         |
|                |                                                 | | geX-<f>/<n>/<p>.<sub-interface-id>         |         |
|                |                                                 | |                                            |         |
|                |                                                 | | bundle-<bundle-id>                         |         |
|                |                                                 | |                                            |         |
|                |                                                 | | bundle-<bundle-id>.<sub-interface-id>      |         |
|                |                                                 | |                                            |         |
|                |                                                 | | lo<lo-interface-id>                        |         |
|                |                                                 | |                                            |         |
|                |                                                 | | irb<irb-interface-id>                      |         |
|                |                                                 | |                                            |         |
|                |                                                 | | ph<phxy-interface-id>.<sub-interface-id>   |         |
+----------------+-------------------------------------------------+----------------------------------------------+---------+

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
| 18.0    | Added IRB support  |
+---------+--------------------+
| 25.3    | Added PWHE support |
+---------+--------------------+
```

## vrf
```rst
network-services vrf
--------------------

**Minimum user role:** operator

To enter the VRF configuration hierarchy under network-services:

**Command syntax: vrf**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# vrf
    dnRouter(cfg-netsrv-vrf)#


**Removing Configuration**

The remove non-default VRFs and restore default VRFs:
::

    dnRouter(cfg-netsrv)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

# EVPN

## counters
```rst
network-services evpn counters
------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for the EVPN service instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# counters
    dnRouter(cfg-netsrv-evpn-counters)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## service-counters
```rst
network-services evpn counters service-counters
-----------------------------------------------

**Minimum user role:** operator

Service-counters enabled is the default setting for EVPN services.
By disabling this knob, service-counters will be disabled for all EVPN instances, that do not have a per-instance configuration.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn counters

**Parameter table**

+------------------+-----------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                           | Range        | Default  |
+==================+=======================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for EVPN services | | enabled    | disabled |
|                  |                                                                       | | disabled   |          |
+------------------+-----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# counters
    dnRouter(cfg-netsrv-evpn-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to its default value
::

    no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## evpn
```rst
network-services evpn
---------------------

**Minimum user role:** operator

EVPN (Ethernet Virtual Private Network) is a layer 2 VPN service that connects layer2 interface(s) of one PE with the layer 2 interface(s) of other PEs, across the layer 3 core MPLS network. The EVPN service uses an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN service configuration mode:

**Command syntax: evpn**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn
    dnRouter(cfg-network-services-evpn)#


**Removing Configuration**

To remove all EVPN services:
::

    dnRouter(cfg-network-services)# no evpn

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## description
```rst
network-services evpn instance description
------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| description | evpn description | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# description "my evpn service"
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-netsrv-evpn-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## e-tree-leaf
```rst
network-services evpn instance e-tree-leaf
------------------------------------------

**Minimum user role:** operator

An e-tree-leaf is not defined or disabled as the default setting for all evpn instances that are created.  
By defining this knob, the e-tree-leaf is enabled, and all interfaces associated with this EVPN instance will by default be defined as leaf interfaces
(unless configured otherwise per AC) and any traffic will need to be forwarded to root ACs.

**Command syntax: e-tree-leaf**

**Command mode:** config

**Hierarchies**

- network-services evpn instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# e-tree-leaf
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To revert the e-tree-leaf configuration to its default of root
::

    dnRouter(cfg-netsrv-evpn-inst)# no e-tree-leaf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services evpn instance
------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN instance

**Command syntax: instance [evpn-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Note**

- The EVPN instance must use a unique name.

**Parameter table**

+-----------+----------------------------------------------------------+------------------+---------+
| Parameter | Description                                              | Range            | Default |
+===========+==========================================================+==================+=========+
| evpn-name | The name of the evpn -- used to address the evpn service | | string         | \-      |
|           |                                                          | | length 1-255   |         |
+-----------+----------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)#


**Removing Configuration**

To revert the specified EVPN instance to default:
::

    dnRouter(cfg-netsrv-evpn-inst)# no instance evpn1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-handling
```rst
network-services evpn mac-handling
----------------------------------

**Minimum user role:** operator

Enter the mac-learning hierarchy to modify the default mac-learning attributes for any new EVPN instances that are subsequently created.

**Command syntax: mac-handling**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To revert the mac-handling configurations to defaults
::

    no mac-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-learning
```rst
network-services evpn mac-handling mac-learning
-----------------------------------------------

**Minimum user role:** operator

Mac-learning enabled is the default setting for EVPN instances.
By defining this knob, mac-learning will be disabled for all new EVPN instances, it will not effect existing services.

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Parameter table**

+--------------+----------------------+--------------+---------+
| Parameter    | Description          | Range        | Default |
+==============+======================+==============+=========+
| mac-learning | Disable MAC Learning | | enabled    | enabled |
|              |                      | | disabled   |         |
+--------------+----------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# mac-learning enabled
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled
::

    no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-table-aging-time
```rst
network-services evpn mac-handling mac-table-aging-time
-------------------------------------------------------

**Minimum user role:** operator

"Configure the default aging time for the entries in the MAC Table that will be set for any new EVPN instances.
Allowed aging time values are: 0 (no aging), 60, 120, 320, 640, 1280 seconds.
If the aging time is set to zero, no aging will be applied. The entries will remain until removed manually via the clear command.
The aging mechanism implementation has some variabilities such that the actual aging time is:

60 +/- 20 seconds 
120 +/- 40 seconds 
320 +/- 160 seconds 
640 +/- 320 seconds 
1280 +/- 640 seconds"

**Command syntax: mac-table-aging-time [mac-table-aging-time]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Parameter table**

+----------------------+--------------------------------------------------------------------------------+----------------------------+---------+
| Parameter            | Description                                                                    | Range                      | Default |
+======================+================================================================================+============================+=========+
| mac-table-aging-time | the default mac-table aging time (in seconds), to be applied to EVPN instances | 0, 60, 120, 320, 640, 1280 | 320     |
+----------------------+--------------------------------------------------------------------------------+----------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# mac-table-aging-time 120
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To restore the default MAC Table aging time to its default value.
::

    dnRouter(dnRouter(cfg-netsrv-evpn-mh)# no mac-table-aging-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-table-limit
```rst
network-services evpn mac-handling mac-table-limit
--------------------------------------------------

**Minimum user role:** operator

Configure the maximum number of entries in the MAC Table for any new EVPN instances. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-handling

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter       | Description                                                                      | Range     | Default |
+=================+==================================================================================+===========+=========+
| mac-table-limit | the maximum number of entries allowed in the mac-table, to be applied to EVPN    | 20-220000 | 64000   |
|                 | instances                                                                        |           |         |
+-----------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-handling
    dnRouter(cfg-netsrv-evpn-mh)# mac-table-limit 10000
    dnRouter(cfg-netsrv-evpn-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-netsrv-evpn-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-ip-handling
```rst
network-services evpn mac-ip-handling
-------------------------------------

**Minimum user role:** operator

The mac-ip-handling Table holds the mac-ip-handling pairs as learnt from ARP/ NDP messages on local ACs and as received in BGP Route-Type-2 mac-ip-handling Advertisements from peers.
To enter the mac-ip-handling Table configuration mode, to set the default values for these attributes. These attributes can be modified by the per instance configurations. 

**Command syntax: mac-ip-handling**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-ip-handling
    dnRouter(cfg-netsrv-evpn-macip)#


**Removing Configuration**

To return the default mac-ip-handling Table configurations to their default values
::

    dnRouter(cfg-netsrv-evpn)# no mac-ip-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## mac-ip-table-aging-time
```rst
network-services evpn mac-ip-handling mac-ip-table-aging-time
-------------------------------------------------------------

**Minimum user role:** operator

"Configure the default MAC-IP Table mac-ip-table-aging-time for all the EVPN instances. The mac-ip-table-aging-time can be modified using the per instance knob."

**Command syntax: mac-ip-table-aging-time [mac-ip-table-aging-time]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-ip-handling

**Parameter table**

+-------------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter               | Description                                                                      | Range | Default |
+=========================+==================================================================================+=======+=========+
| mac-ip-table-aging-time | the default MAC-IP table mac-ip-table-aging-time (in minutes) for all EVPN       | 1-240 | 20      |
|                         | services.                                                                        |       |         |
+-------------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-ip
    dnRouter(cfg-netsrv-evpn-macip)# mac-ip-table-aging-time 120
    dnRouter(cfg-netsrv-evpn-macip)#


**Removing Configuration**

To restore the MAC-IP Table mac-ip-table-aging-time to its default value.
::

    dnRouter(cfg-netsrv-evpn-macip)# no mac-ip-table-aging-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## mac-ip-table-limit
```rst
network-services evpn mac-ip-handling mac-ip-table-limit
--------------------------------------------------------

**Minimum user role:** operator

"Configure the default MAC-IP Table limit for all the EVPN instances. The table limit can be modified using the per instance knob."

**Command syntax: mac-ip-table-limit [mac-ip-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services evpn mac-ip-handling

**Parameter table**

+--------------------+--------------------------------------------------------+------------+---------+
| Parameter          | Description                                            | Range      | Default |
+====================+========================================================+============+=========+
| mac-ip-table-limit | the default MAC-IP table limit for all EVPN instances. | 16-1048575 | 8192    |
+--------------------+--------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# mac-ip-handling
    dnRouter(cfg-netsrv-evpn-macip)# mac-ip-table-limit 20000
    dnRouter(cfg-netsrv-evpn-macip)#


**Removing Configuration**

To restore the default MAC-IP Table limit to its default value.
::

    dnRouter(cfg-netsrv-evpn-macip)# no table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
```

## broadcast-packet-rate
```rst
network-services evpn storm-control broadcast-packet-rate
---------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum broadcast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: broadcast-packet-rate [broadcast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services evpn storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| broadcast-packet-rate | Allowed packet rate of broadcast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# storm-control
    dnRouter(cfg-netsrv-evpn-sc)# broadcast-packet-rate 10000
    dnRouter(cfg-netsrv-evpn-sc)#


**Removing Configuration**

To remove the broadcast-packet-rate limit.
::

    dnRouter(cfg-netsrv-evpn-sc)# no broadcast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## multicast-packet-rate
```rst
network-services evpn storm-control multicast-packet-rate
---------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum multicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: multicast-packet-rate [multicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services evpn storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| multicast-packet-rate | Allowed packet rate of multicast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# storm-control
    dnRouter(cfg-netsrv-evpn-sc)# multicast-packet-rate 10000
    dnRouter(cfg-netsrv-evpn-sc)#


**Removing Configuration**

To remove the multicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-evpn-sc)# no multicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## storm-control
```rst
network-services evpn storm-control
-----------------------------------

**Minimum user role:** operator

Storm Control rate separately limits each of the broadcast, multicast and unknown-unicast packets.
As these packets are replicated to flood all the interfaces attached to the instance, it is important
to ensure that these packets are rate limited. The rate limits configured at this level are applied
to all instances as their default unless configured otherwise at the instance or interface levels.

**Command syntax: storm-control**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# storm-control
    dnRouter(cfg-netsrv-evpn-sc)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn)# no storm-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## unknown-unicast-packet-rate
```rst
network-services evpn storm-control unknown-unicast-packet-rate
---------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum unknown-unicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: unknown-unicast-packet-rate [unknown-unicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services evpn storm-control

**Parameter table**

+-----------------------------+------------------------------------------------+--------------+---------+
| Parameter                   | Description                                    | Range        | Default |
+=============================+================================================+==============+=========+
| unknown-unicast-packet-rate | Allowed packet rate of unknown-unicast packets | 10-100000000 | \-      |
+-----------------------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-evpn)# storm-control
    dnRouter(cfg-netsrv-evpn-sc)# unknown-unicast-packet-rate 10000
    dnRouter(cfg-netsrv-evpn-sc)#


**Removing Configuration**

To remove the unknown-unicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-evpn-sc)# no unknown-unicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## transport-protocol
```rst
network-services evpn transport-protocol
----------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS or VxLAN

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# transport-protocol
    dnRouter(cfg-netsrv-evpn-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.4    | Command introduced |
+---------+--------------------+
```

# MULTIHOMING

## algorithm highest preference
```rst
network-services multihoming designated-forwarder algorithm highest-preference value
------------------------------------------------------------------------------------

**Minimum user role:** operator

Defines the default value to be the highest-preference algorithm, for the algorithm that the user would like to use to choose the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm highest-preference value [preference-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+------------------+----------------------+---------+---------+
| Parameter        | Description          | Range   | Default |
+==================+======================+=========+=========+
| preference-value | The preference value | 0-65535 | \-      |
+------------------+----------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm highest-preference value 10000
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## algorithm mod
```rst
network-services multihoming designated-forwarder algorithm mod
---------------------------------------------------------------

**Minimum user role:** operator

Defines the default value to be the mod algorithm, for the algorithm that the user would like to use to choose the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm mod**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm mod
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## algorithm
```rst
network-services multihoming designated-forwarder algorithm
-----------------------------------------------------------

**Minimum user role:** operator

Defines the default value for the algorithm that the user would like to use for choosing the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm [algorithm]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+-----------+---------------------------------------+----------------------+---------+
| Parameter | Description                           | Range                | Default |
+===========+=======================================+======================+=========+
| algorithm | algorithm to calculate the DF and BDF | mod                  | mod     |
|           |                                       | highest-preference   |         |
+-----------+---------------------------------------+----------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm mod
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## designated-forwarder
```rst
network-services multihoming designated-forwarder
-------------------------------------------------

**Minimum user role:** operator

To enter the designated-forwarder configuration mode:

**Command syntax: designated-forwarder**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To remove all default designated forwarder configurations:
::

    dnRouter(cfg-netsrv-mh)# no designated-forwader

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## df-propagation
```rst
network-services multihoming designated-forwarder df-propagation
----------------------------------------------------------------

**Minimum user role:** operator

Set whether df-propagation shall be enabled or disabled. 
When enabled, if this PE is not the DF then LACP signals OOS to the CE.

**Command syntax: df-propagation [df-propagation]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+----------------+------------------------------------------------------------------+------------+----------+
| Parameter      | Description                                                      | Range      | Default  |
+================+==================================================================+============+==========+
| df-propagation | Whether non-DF should be propagated to CE using LACP out-of-sync | enabled    | disabled |
|                |                                                                  | disabled   |          |
+----------------+------------------------------------------------------------------+------------+----------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# df-propagation enabled
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To revert the df-propagation configuration to its default of disabled.
::

    dnRouter(cfg-mh-int-df)# no df-propagation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## election-time
```rst
network-services multihoming designated-forwarder election-time
---------------------------------------------------------------

**Minimum user role:** operator

Set the default value for the election time upon configuration - how many seconds to wait for the Route Type 4 response from the PE devices.
This value can be modified per interface by using the per-interface knob.

**Command syntax: election-time [election-time]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+---------------+-------------------------------------------+-------+---------+
| Parameter     | Description                               | Range | Default |
+===============+===========================================+=======+=========+
| election-time | time in seconds to wait for Type 4 routes | 0-300 | 3       |
+---------------+-------------------------------------------+-------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# election-time 5
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To revert the default election-time configuration to its default of 3 seconds.
::

    dnRouter(cfg-netsrv-mh-df)# no election-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## no-preemption
```rst
network-services multihoming designated-forwarder no-preemption
---------------------------------------------------------------

**Minimum user role:** operator

Set the default value for whether no-premption is enabled or disabled.
This value can be modified per interface by setting the per-interface knob.

**Command syntax: no-preemption [no-preemption]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+---------------+------------------------------------------------------------------+--------------+----------+
| Parameter     | Description                                                      | Range        | Default  |
+===============+==================================================================+==============+==========+
| no-preemption | Whether this PE, when it is the DF, requests not to be preempted | | enabled    | disabled |
|               |                                                                  | | disabled   |          |
+---------------+------------------------------------------------------------------+--------------+----------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# no-preemption enabled
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To revert the default no-preemption configuration to disabled.
::

    dnRouter(cfg-netsrv-mh-df)# no no-preemption

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
```

## esi arbitrary
```rst
network-services multihoming interface esi arbitrary value
----------------------------------------------------------

**Minimum user role:** operator

Sets the ESI of the interface.

**Command syntax: esi arbitrary value [esi-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Note**

- Only the Arbitrary Type requires a Value.

**Parameter table**

+-----------+-----------------------------------------+-------+---------+
| Parameter | Description                             | Range | Default |
+===========+=========================================+=======+=========+
| esi-value | Define the value for the Arbitrary Type | \-    | \-      |
+-----------+-----------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# esi arbitrary value 11:22:33:44:55:66:77:88:99
    dnRouter(cfg-netsrv-mh-int)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no esi

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## esi lacp
```rst
network-services multihoming interface esi lacp
-----------------------------------------------

**Minimum user role:** operator

Sets the ESI of the interface. 

**Command syntax: esi lacp [esi-lacp-source]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter       | Description                                                                      | Range     | Default |
+=================+==================================================================================+===========+=========+
| esi-lacp-source | Select whether the LACP System-id and Port key shall be taken from the remote CE | remote-id | \-      |
|                 | (future: or from the local side)                                                 |           |         |
+-----------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# esi lacp remote-id
    dnRouter(cfg-netsrv-mh-int)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no esi

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## esi
```rst
network-services multihoming interface esi value
------------------------------------------------

**Minimum user role:** operator

Sets the ESI of the interface.

**Command syntax: esi [esi-type] value [esi-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Note**

- Only the Arbitrary Type requires a Value.

**Parameter table**

+-----------+-----------------------------------------+-----------+---------+
| Parameter | Description                             | Range     | Default |
+===========+=========================================+===========+=========+
| esi-type  | the ESI                                 | arbitrary | \-      |
+-----------+-----------------------------------------+-----------+---------+
| esi-value | Define the value for the Arbitrary Type | \-        | \-      |
+-----------+-----------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no esi

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## interface
```rst
network-services multihoming interface
--------------------------------------

**Minimum user role:** operator

Configure a multihomed interface.

 - An interface must be a l2-service enabled interface or a ph interface.



**Command syntax: interface [name]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Note**

- Support only interface of type <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y/phX/phX.Y>.

**Parameter table**

+-----------+------------------------------------------------+------------------+---------+
| Parameter | Description                                    | Range            | Default |
+===========+================================================+==================+=========+
| name      | Associate an interface to the EVPN Multihoming | | string         | \-      |
|           |                                                | | length 1-255   |         |
+-----------+------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface bundle-1
    dnRouter(cfg-netsrv-mh-int)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0.10
    dnRouter(cfg-evpn-mh-int)#



**Removing Configuration**

To remove the interface from its association to multihoming
::

    dnRouter(cfg-netsrv-mh)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## no-startup-delay
```rst
network-services multihoming interface no-startup-delay
-------------------------------------------------------

**Minimum user role:** operator

Prevents the startup-delay to be applied on this multihomed parent interface (physical interfaces or bundles).
The delay (if configured under multihoming) would normally have been applied upon startup after a power-cycle,
cold-restart or warm-restart on all the multihomed interfaces.

**Command syntax: no-startup-delay**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# no-startup-delay


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no no-startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
```

## redundancy-mode
```rst
network-services multihoming interface redundancy-mode
------------------------------------------------------

**Minimum user role:** operator

Sets the redundancy-mode for the AC interface -  all-active, single-active or port-active. 

**Command syntax: redundancy-mode [redundancy-mode]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Parameter table**

+-----------------+----------------------------------------------------------+-------------------+---------+
| Parameter       | Description                                              | Range             | Default |
+=================+==========================================================+===================+=========+
| redundancy-mode | interface type, single-active, port-active or all-active | | single-active   | \-      |
|                 |                                                          | | all-active      |         |
|                 |                                                          | | port-active     |         |
+-----------------+----------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# redundancy-mode single-active


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no redundancy-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## multihoming
```rst
network-services multihoming
----------------------------

**Minimum user role:** operator

When an CE device is connected to two different core PE devices for redundancy and loadsharing purposes, this is referred to as a multihomw=ed CE device .
Under the multihoming branch the ACs which are multihomed can be defined.
To enter the multihoming configuration mode:

**Command syntax: multihoming**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# multihoming
    dnRouter(cfg-network-services-mh)#


**Removing Configuration**

To remove all multihoming configurations:
::

    dnRouter(cfg-network-services)# no multihoming

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## redundancy-mode
```rst
network-services multihoming redundancy-mode
--------------------------------------------

**Minimum user role:** operator

Sets the default redundancy-mode - single-active or all-active.

**Command syntax: redundancy-mode [redundancy-mode]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Parameter table**

+-----------------+---------------------------------------------+-------------------+------------+
| Parameter       | Description                                 | Range             | Default    |
+=================+=============================================+===================+============+
| redundancy-mode | interface type, single-active or all-active | | single-active   | all-active |
|                 |                                             | | all-active      |            |
|                 |                                             | | port-active     |            |
+-----------------+---------------------------------------------+-------------------+------------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# redundancy-mode single-active
    dnRouter(cfg-netsrv-mh)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no redundancy-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## startup-delay
```rst
network-services multihoming startup-delay
------------------------------------------

**Minimum user role:** operator

Sets the startup-delay to be applied on all multihomed parent interfaces (physical interfaces or bundles).
The delay is applied upon startup after power-cycle, cold-restart or warm-restart.

**Command syntax: startup-delay [startup-delay]**

**Command mode:** config

**Hierarchies**

- network-services multihoming

**Parameter table**

+---------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                                      | Range   | Default |
+===============+==================================================================================+=========+=========+
| startup-delay | Delay in seconds to apply to multihomed interfaces upon startup of the           | 60-1800 | \-      |
|               | interface, while keeping the laser-off                                           |         |         |
+---------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# startup-delay 500
    dnRouter(cfg-netsrv-mh)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh)# no startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
```

# VPWS

## description
```rst
network-services vpws instance description
------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN VPWS:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Parameter table**

+-------------+------------------+------------------+---------+
| Parameter   | Description      | Range            | Default |
+=============+==================+==================+=========+
| description | vpws description | | string         | \-      |
|             |                  | | length 1-255   |         |
+-------------+------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# description "my vpws service"


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-network-services-vpws-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services vpws instance
------------------------------

**Minimum user role:** operator

To configure the name of a L2VPN VPWS service:

**Command syntax: instance [vpws-name]**

**Command mode:** config

**Hierarchies**

- network-services vpws

**Note**

- The VPWS service must use a unique name.

**Parameter table**

+-----------+----------------------------------------------------------+------------------+---------+
| Parameter | Description                                              | Range            | Default |
+===========+==========================================================+==================+=========+
| vpws-name | The name of the vpws -- used to address the vpws service | | string         | \-      |
|           |                                                          | | length 1-255   |         |
+-----------+----------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)#


**Removing Configuration**

To revert the specified VPWS service to default:
::

    dnRouter(cfg-network-services-vpws)# no instance VPWS_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## interface
```rst
network-services vpws instance interface
----------------------------------------

**Minimum user role:** operator

To configure an interface to use the VPWS service, also known as the Attachment-Circuit. This can be any in-band interface, such as physical, sub-interface, bundle, or breakout interface.

The Pseudowire type is defined by default according to the AC interface type:
- physical interface will result in PW type Ethernet (type 5)
- sub-interface type vlan will result in PW type Vlan (type 4)
- sub-interface type untagged will result in PW type Ethernet (type 5)

Packets received on PW to be sent from AC:
- for AC vlan - by default, update packet tagging to match AC tag
- for AC vlan - by default, packet is sent without any modifications

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Note**

- Only interface types <geX-X/X/X/bundle-X/<geX-X/X/X.Y>/<bundle-X.Y> are supported.

- The Pseudowire is not established until the interface is configured.

- The interface must be a L2-service enabled interface.

- The interface cannot be assign to multiple services.

**Parameter table**

+-----------+-------------------------------------+------------------+---------+
| Parameter | Description                         | Range            | Default |
+===========+=====================================+==================+=========+
| interface | the vpws service attachment circuit | | string         | \-      |
|           |                                     | | length 1-255   |         |
+-----------+-------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# interface ge100-0/0/0

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# VPWS_1
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)#  interface bundle-1

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# VPWS_1
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# interface ge100-0/0/0.1


**Removing Configuration**

To remove the interface configuration:
::

    dnRouter(cfg-network-services-vpws-inst)# no interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

## vpws
```rst
network-services vpws
---------------------

**Minimum user role:** operator

VPWS (Virtual Private Wire Service) is a point-to-point layer2 VPN service that connects a layer-2 interface of one PE with the layer-2 interface of another PE, across the layer-3 core mpls network. The VPWS service uses a Pseudowire (PW) point-to-point tunnel to emulate a physical connection and create an intermediate transport between the two PEs.

To enter the VPWS service configuration mode:

**Command syntax: vpws**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)#


**Removing Configuration**

To remove all VPWS services:
::

    dnRouter(cfg-network-services)# no vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
```

# BRIDGE-DOMAIN

## bridge-domain
```rst
network-services bridge-domain
------------------------------

**Minimum user role:** operator

Bridge domains (Ethernet Virtual Private Network) refer to a Layer 2 broadcast domain consisting of a set of physical ports (“All-to-one bundling”, “port-mode”), and virtual ports (Attachment Circuits).
Data frames are switched within a bridge domain based on the destination MAC address.  Source MAC address learning is performed on all incoming packets.
Multicast, broadcast, and unknown destination unicast frames are flooded within the bridge domain.
Incoming frames are mapped to a bridge domain by their incoming VLAN/VLANs.
Traffic cannot leak between one bridge domain to another. Each bridge domain is totally independent (a leak is possible only via routing through IRBs).
The bridge domain connects the layer 2 interface(s) of one PE with the layer 2 interface(s) of other PEs, across the layer 3 core mpls network. The EVPN service uses an MPLS or VxLAN transport layer and a BGP control layer.
To enter the Bridge Domain service configuration mode:

**Command syntax: bridge-domain**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# bridge-domain
    dnRouter(cfg-network-services-bd)#


**Removing Configuration**

To remove all EVPN services:
::

    dnRouter(cfg-network-services)# no brifge-domain

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
network-services bridge-domain instance admin-state
---------------------------------------------------

**Minimum user role:** operator

Configure the Bridge-Domain Instance admin-state. Once disabled, the BD service is down, no traffic will flow

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Parameter table**

+-------------+---------------------------+--------------+---------+
| Parameter   | Description               | Range        | Default |
+=============+===========================+==============+=========+
| admin-state | Disable the Bridge Domain | | enabled    | enabled |
|             |                           | | disabled   |         |
+-------------+---------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-netsrv-bd-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## description
```rst
network-services bridge-domain instance description
---------------------------------------------------

**Minimum user role:** operator

To add an optional description of the Bridge Domain Instance

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Parameter table**

+-------------+---------------------------+------------------+---------+
| Parameter   | Description               | Range            | Default |
+=============+===========================+==================+=========+
| description | bridge-domain description | | string         | \-      |
|             |                           | | length 1-255   |         |
+-------------+---------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# description "my bridge-domain service"


**Removing Configuration**

To revert description to default:
::

    dnRouter(cfg-netsrv-bd-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services bridge-domain instance
---------------------------------------

**Minimum user role:** operator

Configure a Bridge-Domain service

**Command syntax: instance [bd-name]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Note**

- The Bridge-Domain service must use a unique name.

- The number of Bridge-Domain instances that can be defined is limited to 1000.

**Parameter table**

+-----------+------------------------------------------------------+------------------+---------+
| Parameter | Description                                          | Range            | Default |
+===========+======================================================+==================+=========+
| bd-name   | The name of the bd -- used to address the bd service | | string         | \-      |
|           |                                                      | | length 1-255   |         |
+-----------+------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)#


**Removing Configuration**

To revert the specified Bridge-Domain service to default:
::

    dnRouter(cfg-netsrv-bd)# no instance bd1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## router-interface
```rst
network-services bridge-domain instance router-interface
--------------------------------------------------------

**Minimum user role:** operator

Configure a router-interface for the Bridge-Domain service instance

 - The Interface must be an IRB interface.

 - An IRB cannot be assigned to multiple Bridge-Domain services.

**Command syntax: router-interface [router-interface]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Note**

- Only supports <irbX> type interface.

**Parameter table**

+------------------+-------------------+------------------+---------+
| Parameter        | Description       | Range            | Default |
+==================+===================+==================+=========+
| router-interface | the IRB interface | | string         | \-      |
|                  |                   | | length 1-255   |         |
+------------------+-------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# router-interface irb10
    dnRouter(cfg-evpn-inst-ge100-0/0/0)#



**Removing Configuration**

To remove the interface from its association with the bridge-domain instance
::

    dnRouter(cfg-netsrv-bd-inst)# no router-interface irb10

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-handling
```rst
network-services bridge-domain mac-handling
-------------------------------------------

**Minimum user role:** operator

Enter the mac-learning hierarchy to modify the mac-learning attributes for this bridge-domain instance.

**Command syntax: mac-handling**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dev-dnRouter(cfg-netsrv-bd)# mac-handling
    dev-dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To revert the mac-handling configurations to defaults
::

    dnRouter(cfg-netsrv-bd)# no mac-handling

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-learning
```rst
network-services bridge-domain mac-handling mac-learning
--------------------------------------------------------

**Minimum user role:** operator

This default mac-learning setting defines the default value that will be set for any new bridge-domain instances. 

**Command syntax: mac-learning [mac-learning]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+--------------+----------------------+--------------+---------+
| Parameter    | Description          | Range        | Default |
+==============+======================+==============+=========+
| mac-learning | Disable MAC Learning | | enabled    | enabled |
|              |                      | | disabled   |         |
+--------------+----------------------+--------------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dev-dnRouter(cfg-netsrv-bd)# mac-handling
    dev-dnRouter(cfg-netsrv-bd-mh)# mac-learning disabled
    dev-dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To revert the mac-learning configuration to its default of enabled.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-learning

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-table-aging-time
```rst
network-services bridge-domain mac-handling mac-table-aging-time
----------------------------------------------------------------

**Minimum user role:** operator

"Configure the default aging time for the entries in the MAC Table that will be set for any new bridge-domain instances.
Allowed aging time values are: 0 (no aging), 60, 120, 320, 640, 1280 seconds.
If the aging time is set to zero, no aging will be applied. The entries will remain until removed manually via the clear command.
The aging mechanism implementation has some variabilities such that the actual aging time is:

 60 +/- 20 seconds 
 120 +/- 40 seconds 
 320 +/- 160 seconds 
 640 +/- 320 seconds 
 1280 +/- 640 seconds"

**Command syntax: mac-table-aging-time [mac-table-aging-time]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+
| Parameter            | Description                                                                      | Range                      | Default |
+======================+==================================================================================+============================+=========+
| mac-table-aging-time | the default mac-table aging time (in seconds), to be applied to Bridge-Domain    | 0, 60, 120, 320, 640, 1280 | 320     |
|                      | instances.                                                                       |                            |         |
+----------------------+----------------------------------------------------------------------------------+----------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bd
    dnRouter(cfg-netsrv-bd)# mac-handling
    dnRouter(cfg-netsrv-bd-mh)# mac-table-aging-time 320
    dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To restore the MAC Table aging time to its default value.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-table-aging-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## mac-table-limit
```rst
network-services bridge-domain mac-handling mac-table-limit
-----------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 20-6400)for the maximum number of entries in the MAC Table for any new Bridge-Domain instances defined. When this limit is reached, new MAC addresses will not be added to the MAC Table.

**Command syntax: mac-table-limit [mac-table-limit]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain mac-handling

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter       | Description                                                                      | Range    | Default |
+=================+==================================================================================+==========+=========+
| mac-table-limit | the default value for the maximum number of entries allowed in the mac-table     | 20-64000 | 64000   |
|                 | that will be applied to any new Bridge-Domain instances subsequently created.    |          |         |
+-----------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# mac-handling
    dnRouter(cfg-netsrv-bd-mh)# mac-table-limit 10000
    dnRouter(cfg-netsrv-bd-mh)#


**Removing Configuration**

To restore the MAC Table limit to its default value.
::

    dnRouter(cfg-netsrv-bd-mh)# no mac-table-limit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
```

## broadcast-packet-rate
```rst
network-services bridge-domain storm-control broadcast-packet-rate
------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum broadcast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: broadcast-packet-rate [broadcast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| broadcast-packet-rate | Allowed packet rate of broadcast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)# broadcast-packet-rate 10000
    dnRouter(cfg-netsrv-bd-sc)#


**Removing Configuration**

To remove the broadcast-packet-rate limit.
::

    dnRouter(cfg-netsrv-bd-sc)# no broadcast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## multicast-packet-rate
```rst
network-services bridge-domain storm-control multicast-packet-rate
------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum multicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: multicast-packet-rate [multicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| multicast-packet-rate | Allowed packet rate of multicast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)# multicast-packet-rate 10000
    dnRouter(cfg-netsrv-bd-sc)#


**Removing Configuration**

To remove the multicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-bd-sc)# no multicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## storm-control
```rst
network-services bridge-domain storm-control
--------------------------------------------

**Minimum user role:** operator

Storm Control rate separately limits each of the broadcast, multicast and unknown-unicast packets.
As these packets are replicated to flood all the interfaces attached to the service, it is important
to ensure that these packets are rate limited. The rate limits configured at this level are applied
to all instances as their default unless configured otherwise at the instance or interface levels.

**Command syntax: storm-control**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-bd)# no storm-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

## unknown-unicast-packet-rate
```rst
network-services bridge-domain storm-control unknown-unicast-packet-rate
------------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum unknown-unicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: unknown-unicast-packet-rate [unknown-unicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain storm-control

**Parameter table**

+-----------------------------+------------------------------------------------+--------------+---------+
| Parameter                   | Description                                    | Range        | Default |
+=============================+================================================+==============+=========+
| unknown-unicast-packet-rate | Allowed packet rate of unknown-unicast packets | 10-100000000 | \-      |
+-----------------------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)# unknown-unicast-packet-rate 10000
    dnRouter(cfg-netsrv-bd-sc)#


**Removing Configuration**

To remove the unknown-unicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-bd-sc)# no unknown-unicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
```

# EVPN-VPWS

## counters
```rst
network-services evpn-vpws counters
-----------------------------------

**Minimum user role:** operator

Defines whether counters should be allocated for the EVPN-VPWS service instances by default. 

**Command syntax: counters**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# counters
    dnRouter(cfg-netsrv-evpn-vpws-counters)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-evpn-vpws)# no counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## service-counters
```rst
network-services evpn-vpws counters service-counters
----------------------------------------------------

**Minimum user role:** operator

Service-counters enabled is the default setting for EVPN-VPWS services.
By disabling this knob, service-counters will be disabled for all EVPN-VPWS instances, that do not have a per-instance configuration.

**Command syntax: service-counters [service-counters]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws counters

**Parameter table**

+------------------+-----------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                           | Range        | Default  |
+==================+=======================================================================+==============+==========+
| service-counters | Define whether service-counters should be allocated for EVPN services | | enabled    | disabled |
|                  |                                                                       | | disabled   |          |
+------------------+-----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# counters
    dnRouter(cfg-netsrv-evpn-vpws-counters) service-counters disabled


**Removing Configuration**

To revert the service-counters configuration to its default of disabled
::

    no service-counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
```

## evpn-vpws
```rst
network-services evpn-vpws
--------------------------

**Minimum user role:** operator

EVPN-VPWS (Ethernet Virtual Private Network) is a point-to-point layer 2 VPN service that connects one layer 2 interface(s) of
a PE device with one layer 2 interface(s) of another PE device, across the layer 3 core MPLS network. The EVPN service uses
an MPLS or VxLAN transport layer and a BGP control layer.

To enter the EVPN-VPWS service configuration mode:

**Command syntax: evpn-vpws**

**Command mode:** config

**Hierarchies**

- network-services

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To remove all EVPN VPWS services:
::

    dnRouter(cfg-network-services)# no evpn-vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## admin-state
```rst
network-services evpn-vpws instance admin-state
-----------------------------------------------

**Minimum user role:** operator

Define the EVPN_VPWS service instance admin-state. By default the admin-state is enabled.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Parameter table**

+-------------+--------------------------------+--------------+---------+
| Parameter   | Description                    | Range        | Default |
+=============+================================+==============+=========+
| admin-state | evpn-vpws instance admin-state | | enabled    | enabled |
|             |                                | | disabled   |         |
+-------------+--------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# admin-state disabled
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To revert the admin-state to its default: enabled
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## description
```rst
network-services evpn-vpws instance description
-----------------------------------------------

**Minimum user role:** operator

To add an optional description of the L2VPN EVPN VPWS:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Parameter table**

+-------------+-----------------------+------------------+---------+
| Parameter   | Description           | Range            | Default |
+=============+=======================+==================+=========+
| description | evpn-vpws description | | string         | \-      |
|             |                       | | length 1-255   |         |
+-------------+-----------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# description "my evpn-vpws service"
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## instance
```rst
network-services evpn-vpws instance
-----------------------------------

**Minimum user role:** operator

Configure a L2VPN EVPN-VPWS instance.

**Command syntax: instance [evpn-vpws-name]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Note**

- The EVPN VPWS service must use a unique name.

**Parameter table**

+----------------+--------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                        | Range            | Default |
+================+====================================================================+==================+=========+
| evpn-vpws-name | The name of the evpn-vpws -- used to address the evpn-vpws service | | string         | \-      |
|                |                                                                    | | length 1-255   |         |
+----------------+--------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To revert the specified EVPN VPWS service to default:
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no instance evpn-vpws1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## l2-mtu
```rst
network-services evpn-vpws instance l2-mtu
------------------------------------------

**Minimum user role:** operator

Configure the MTU value of this instance to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used, no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | \-      |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## l2-mtu
```rst
network-services evpn-vpws l2-mtu
---------------------------------

**Minimum user role:** operator

Configure the default (can be modified per instance) MTU value to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | 0       |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-network-services-evpn-vpws)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

## transport-protocol
```rst
network-services evpn-vpws transport-protocol
---------------------------------------------

**Minimum user role:** operator

The transport-protocol should be set to MPLS.

**Command syntax: transport-protocol**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# transport-protocol
    dnRouter(cfg-netsrv-evpn-vpws-tp)#


**Removing Configuration**

To remove transport-protocol definitions - reverting then to their default values.
::

    dnRouter(cfg-netsrv-evpn-vpws)# no transport-protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
```

