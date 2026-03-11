run start shell
---------------

**Minimum user role:** admin

To access a node's shell container:

**Command syntax: run start shell** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \| ncm [ncm-hostname]}

**Command mode:** recovery

**Note**

- root@node-manager - an NCC prompt. The prompt varies depending on the accessed NCE .

- TACACS+ AAA (recovery mode) is allowed for local users only.

- The command in recovery mode provides access to the shell of the active NCC only.

.. - No TACACS AAA (Recovery mode), should be allowed for local users only

	- "exit" commands reverts back to the Recovery Mode CLI.

**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| Parameter      | Description                                                                                            | Range                                                                        |
+================+========================================================================================================+==============================================================================+
| ncc-id         | Provides access to the shell of the specified NCC                                                      | 0..1                                                                         |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| ncp-id         | Provides access to the shell of the specified NCP                                                      | 0..(max NCP number per cluster type -1), bfd-master                          |
|                | bfd-master - provides access to the ncp that holds all non uBFD, BFD sessions.                         |                                                                              |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| ncf-id         | Provides access to the shell of the specified NCF                                                      | 0..(max NCF number per cluster type -1)                                      |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| container-name | Provides access to the container within the specified node.                                            | A container from the process list that applicable to the specified node name |
|                | The container option is not applicable to NCMs.                                                        |                                                                              |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| ncm-id         | Provides access to the shell of the specified NCM                                                      | a0, b0, a1, b1                                                               |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+
| ncc active     | Provides access to containers in the current active NCC. When set, a container name must be specified. | \-                                                                           |
+----------------+--------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------+

If you do not provide a node name and ID, you will be granted access to the active NCC's shell.

If you do not specify a container within the node, you will be granted access to the following containers by default:

+-----------+--------------------------+
| Node Type | Default Container        |
+===========+==========================+
| NCC       | routing-engine container |
+-----------+--------------------------+
| NCP       | datapath container       |
+-----------+--------------------------+
| NCF       | fabric container         |
+-----------+--------------------------+

To return to the DNOS CLI, use the exit command.

**Example**
::

	dnRouter(RECOVERY)#  run start shell
	root@routing_engine:/#

	root@routing_engine:/# exit
	dnRouter(RECOVERY)#

.. **Help line:** access to shell of the NCC/NCP/NCF/NCM components

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 10.0    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 11.0    | Command added to recovery mode                      |
+---------+-----------------------------------------------------+
| 11.5    | Added option to access containers of the active NCC |
+---------+-----------------------------------------------------+
| 13.0    | Added new ncp option for command - bfd-master       |
+---------+-----------------------------------------------------+
