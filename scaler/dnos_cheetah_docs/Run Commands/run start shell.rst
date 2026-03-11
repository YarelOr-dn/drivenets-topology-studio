run start shell
---------------

**Minimum user role:** admin

To access a node's shell container:

**Command syntax: run start shell** { {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id] \} container [container-name] } | ncm [ncm-id] | {ncc active container [container-name]}

**Command mode:** operation

**Note**

- TACACS+ AAA (recovery mode) is allowed for local users only.

- The command in recovery mode provides access to the shell of the active NCC only.

- root@node-manager - an NCC prompt. The prompt varies depending on the accessed NCE .

.. - "exit" commands reverts back to the DNOS CLI.

	bfd-master - access ncp that holds all non uBFD, BFD sessions

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

	dnRouter# run start shell
	root@routing-engine:/#

	root@routing-engine:/# exit
	dnRouter#

	dnRouter# run start shell ncc 0 container routing-engine
	root@routing-engine:/#

	root@routing-engine:/# exit
	dnRouter#

	dnRouter# run start shell ncc active container node-manager
	root@node-manager:/#

	root@node-manager:/# exit
	dnRouter#

	dnRouter# run start shell ncf 1
	root@fabric-engine:/#

	root@fabric-engine:/# exit
	dnRouter#

	dnRouter# run start shell ncm a1
	root@ncm:/#

	root@ncm:/# exit
	dnRouter#

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
