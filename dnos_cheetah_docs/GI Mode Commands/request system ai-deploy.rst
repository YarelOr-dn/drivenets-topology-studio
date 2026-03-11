request system ai-deploy
------------------------

**Minimum user role:** viewer

Deploys AI SA router with provided system type and name.

**Command syntax: request system ai-deploy system-type [system-type] name [name] node-type [node-type] node-id [node-id] ncc-id [ncc-id]** oob-mgmt-ipv4 {dhcp \| [ipv4-address] [ipv4-default-gateway] \| disabled} oob-mgmt-ipv6 {dhcp \| [ipv6-address] [ipv6-default-gateway] \| disabled } gnmi-port [gnmi-port] netconf-port [netconf-port]

**Command mode:** GI

**Note**

 - Supports cluster system-type (CL-AI-X) on NCP/NCF HW node.

 - Auto-generates router's system-id.

 - Auto-generates router's default self-signed TLS certificate for gRPC/gNMI server.

 - As par tof the deployment user must provide 'node-id' matching existing/planned NCP/NCF cabling.

 - oob-mgmt-ipv4  - apply out-of-band management interface ipv4 settings, options are:
    -  dhcp - retrieve ipv4 local address and default-gateway from DHCP server. Default behavior
    -  ipv4-address - statically set the local ipv4 address and subnet. Must be set together with ipv4-default-gateway
    -  ipv4-default-gateway - statically set the default-gateway ipv4 address. Must be set together with ipv4-address
    -  disabled - disable ipv4 connectivity on the out-of-band management interface

 - node-id - Define the requested ID for the NCP/NCF depending on the node-type. The node-id must comply with NCP/NCF connectivity.

 - ncc-id - Define the requested ID for the NCC. only 0 is an available choice for AI deployment

 - oob-mgmt-ipv6  - apply out-of-band management interface ipv6 settings, options are:
    -  dhcp - retrieve ipv6 local address and default-gateway from DHCP server. Default behavior
    -  ipv6-address - statically set the local ipv6 address and subnet. Must be set together with ipv4-default-gateway
    -  ipv6-default-gateway - statically set the default-gateway ipv4 address. Must be set together with ipv6-address
    -  disabled - disable ipv6 connectivity on the out-of-band management interface

 - Validation: the command shall fail in case both oob-mgmt-ipv4 and oob-mgmt-ipv6 are disabled


**Example**
::

	gi# request system ai-deploy system-type CL-AI-8K-400G name SYS_1 node-type ncf node-id 0
	The following software or firmware will be installed:
	   DNOS 18.2.40
	Warning: Do you want to continue? (Yes/No) [No]?

	gi# request system ai-deploy system-type CL-AI-8K-400G name SYS_1 node-type ncp node-id 1 oob-mgmt-ipv4 ipv4-address 5.5.5.2/24 5.5.5.1 oob-mgmt-ipv6 disabled
	The following software or firmware will be installed:
	   DNOS 18.2.40
	Warning: Do you want to continue? (Yes/No) [No]?

    gi# request system ai-deploy system-type CL-AI-8K-400G name SYS_1 node-type ncf node-id 0 oob-mgmt-ipv4 disabled oob-mgmt-ipv6 disabled
    Error: at least one oob-mgmt-ip address configuration shall exist!


.. **Hidden Note:**

 -  Yes/no validation should exist for the operation.


**Parameter table:**

+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
|       Parameter      | Description                                                                |                    Range                   | Default |
+======================+============================================================================+============================================+=========+
| system-type          | The type of NCR                                                            | CL-AI-8K-400G                              | \-      |
|                      |                                                                            | AI-256-400G-2                              |         |
|                      |                                                                            | AI-72-800G-2                               |         |
|                      |                                                                            | AI-8192-400G-2                             |         |
|                      |                                                                            | AI-768-400G-1                              |         |
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
| node-id              | The ID number of the node, ncp/ncf                                         | NCPs - 0..255                              | \-      |
|                      |                                                                            | NCFs - 0..611                              |         |
+----------------------+----------------------------------------------------------------------------+--------------------------------------------+---------+
| node-type            | The type of the node                                                       | ncp, ncf,                                  | \-      |
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
| 19.10   | Added support for AI                |
+---------+-------------------------------------+
