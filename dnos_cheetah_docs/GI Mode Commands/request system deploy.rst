request system deploy
---------------------

**Minimum user role:** viewer

Deploys DNOS router with provided system type and name.

**Command syntax: request system deploy system-type [system-type] name [name] ncc-id [ncc-id]** oob-mgmt-ipv4 {dhcp \| [ipv4-address] [ipv4-default-gateway] \| disabled} oob-mgmt-ipv6 {dhcp \| [ipv6-address] [ipv6-default-gateway] \| disabled } gnmi-port [gnmi-port] netconf-port [netconf-port]

**Command mode:** GI

**Note**

 - Supports stanalone system-type (SA_X) on NCP HW node, cluster system-type (CL_X) on NCC HW node.

 - Auto-generates router's system-id.

 - Auto-generates router's default self-signed TLS certificate for gRPC/gNMI server.

 - For cluster user must provide NCC-ID matching existing/planned NCC cabling towards NCMs (NCC-0 connects to NCM port 48, NCC-1 connects to NCM port 49).

 - oob-mgmt-ipv4  - apply out-of-band management interface ipv4 settings, options are:
    -  dhcp - retrieve ipv4 local address and default-gateway from DHCP server. Default behavior
    -  ipv4-address - statically set the local ipv4 address and subnet. Must be set together with ipv4-default-gateway
    -  ipv4-default-gateway - statically set the default-gateway ipv4 address. Must be set together with ipv4-address
    -  disabled - disable ipv4 connectivity on the out-of-band management interface

 - ncc-id - Define the requested ID for the NCC, either 0 or 1. The ncc-id must comply with NCC connectivity to the NCM.
    ID 0 NCC is connected to NCMs port 48, ID 1 NCC is connected to NCMs port 49.
    When the NCC is not connected to any NCM, user may set either ID 0 or ID 1, which will define the NCC ID once DNOS starts

 - oob-mgmt-ipv6  - apply out-of-band management interface ipv6 settings, options are:
    -  dhcp - retrieve ipv6 local address and default-gateway from DHCP server. Default behavior
    -  ipv6-address - statically set the local ipv6 address and subnet. Must be set together with ipv4-default-gateway
    -  ipv6-default-gateway - statically set the default-gateway ipv4 address. Must be set together with ipv6-address
    -  disabled - disable ipv6 connectivity on the out-of-band management interface

 - Validation: the command shall fail in case both oob-mgmt-ipv4 and oob-mgmt-ipv6 are disabled


**Example**
::

	gi# request system deploy system-type SA-40C name SYS_1 ncc-id 0
	The following software or firmware will be installed:
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

	gi# request system deploy system-type SA-40C name SYS_1 ncc-id 1 oob-mgmt-ipv4 ipv4-address 5.5.5.2/24 5.5.5.1 oob-mgmt-ipv6 disabled
	The following software or firmware will be installed:
	   DNOS 17.2
	Warning: Do you want to continue? (Yes/No) [No]?

    gi# request request system deploy system-type SA-40C name SYS_1 ncc-id 1 oob-mgmt-ipv4 disabled oob-mgmt-ipv6 disabled
    Error: at least one oob-mgmt-ip address configuration shall exist!


.. **Hidden Note:**

 -  Yes/no validation should exist for the operation.


**Parameter table:**

+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
|       Parameter      | Description                                                                |                    Range                   | Default |
+======================+============================================================================+============================================+=========+
| system-type          | The type of NCR                                                            | SA-40C                                     | \-      |
|                      |                                                                            | SA-10CD                                    |         |
|                      |                                                                            | CL-16                                      |         |
|                      |                                                                            | CL-32                                      |         |
|                      |                                                                            | CL-48                                      |         |
|                      |                                                                            | CL-64                                      |         |
|                      |                                                                            | CL-96                                      |         |
|                      |                                                                            | CL-192                                     |         |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| name                 | The name of the system                                                     | string, 1-32 characters                    | \-      |
|                      |                                                                            | allowed characters: alphanumeric, "-", "_" |         |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| oob-mgmt-ipv4        | The ipv4 management address address allocation mode of the system          | dhcp, A.B.C.D/X, disabled                  | dhcp    |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| ipv4-address         | The ipv4 address of the system                                             | A.B.C.D/X                                  | \-      |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| ipv4-default-gateway | The ipv4 default gateway address of the system                             | A.B.C.D                                    | \-      |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| oob-mgmt-ipv6        | The ipv6 management address address allocation mode of the system          | dhcp, {ipv6-address and prefix format},    | dhcp    |
|                      |                                                                            | disabled                                   |         |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| ipv6-address         | The ipv6 address of the system                                             | {ipv6-address and prefix format}           | \-      |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| ipv6-default-gateway | The ipv6 default gateway address of the system                             | {ipv6-address format}                      | \-      |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| ncc-id               | The ID number of the ncc                                                   | 0,1                                        | \-      |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| gnmi-port            | The gNMI port the server will listen after deployment                      | 50051, 9339                                | 50051   |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| netconf-port         | The NETCONF port the server will listen after deployment                   | 830, 22                                    | 830     |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+

.. **Help line:** Create DNOS router.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 16.1    | Command introduced                  |
+---------+-------------------------------------+
