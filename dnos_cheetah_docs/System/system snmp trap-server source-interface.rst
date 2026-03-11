system snmp trap-server source-interface
----------------------------------------

**Minimum user role:** operator

This command is applicable to the following interfaces:

physical interfaces logical interfaces (sub-interfaces) bundle interfaces bundle sub-interfaces loopback interfaces

By default, the source-interface for SNMP sessions is the system in-band-management source-interface. To override the default behavior and configure a different source-interface for SNMP sessions:

**Command syntax: source-interface [source-interface]**

**Description:** configure system snmp source interface for outgoing snmp sessions per server per VRF.

	- Validation that ip address must be configured on the interface configuration.

	- source-interface must be configured with the same address type as the remote snmp server otherwise the trap won't be sent.

**Parameter table**

+----------------+---------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter      | Description                                                                                                                     | Range                                               | Default |
+================+=================================================================================================================================+=====================================================+=========+
| interface-name | The name of the interface whose source IP address will be used for all SNMP sessions.                                           | A configured interface:                             | \-      |
|                | This interface must be configured with an IPv4 address.                                                                         |                                                     |         |
|                | The source-interface must be configured with the same address type as the remote snmp server, otherwise the trap won't be sent. | ge<interface speed>-<A>/<B>/<C>                     |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>  |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | bundle-<bundle id>                                  |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | bundle-<bundle id>.<sub-interface id>               |         |
|                |                                                                                                                                 |                                                     |         |
|                |                                                                                                                                 | lo<lo-interface id>                                 |         |
+----------------+---------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-snmp-trap-server)# source-interface lo100
    dnRouter(cfg-snmp-trap-server)# source-interface bundle-1
    dnRouter(cfg-snmp-trap-server)# source-interface ge100-0/0/0

    dnRouter(cfg-system-snmp)# trap-server 1.1.1.1 vrf mgmt0
    dnRouter(cfg-snmp-trap-server)# source-interface mgmt0

    dnRouter(cfg-system-snmp-trap-server)#  no source-interface

**Command mode:** config

**TACACS role:** operator

**Removing Configuration**

Configuration is per server per VRF for all outgoing snmp applications (trap-server output etc).

-  By default used global configuration for source interface is used "system inband source-interface" for VRF default and "network-services vrf management-plane source-interface" for non-default in-band management VRF.
    - in case source-interface under trap-server is specified it will override the global source-interface config for that server.
    - Validation: source-interface is associated with the same VRF as the trap server, otherwise commit will fail validation

-  Only mgmt0 source-interface can be supported for mgmt0 VRF and it is the default value.

.. **Help line:** Configure system snmp source interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
