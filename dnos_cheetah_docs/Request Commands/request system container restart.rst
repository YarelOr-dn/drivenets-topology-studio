request system container restart 
---------------------------------

**Minimum user role:** admin

To restart the containers of cluster components:

**Command syntax: request system container restart** {ncc [ncc-id] \| ncp [ncp-id] \| ncf [ncf-id]} **[container-name]**

**Command mode:** operational

**Note**

- You will be prompted to confirm the restart.

- If you do not specify a node, the container(s) on the active NCC will be restarted.

..
	**Internal Note**

	- Yes/no validation should exist for container restart operations

	- Warning should be displayed for container start.

	- datapath reset should shut down physical interfaces during the reset operation on the relevant NCP

	- Datapath reset on NCF should also result in shutting down the physical interfaces on all NCP when resetting NCF in a small cluster.

	- In bigger clusters when resetting the NCF datapath container shutting down the physical interfaces on NCP should take place if the NCF resets reduces the number of fabric interfaces below preconfigured minimum threshold.

**Parameter table**

+-------------------+---------------------------------------------------------------+-------------------------------------------------------------+
|                   |                                                               |                                                             |
| Parameter         | Description                                                   | Range                                                       |
+===================+===============================================================+=============================================================+
|                   |                                                               |                                                             |
| ncc-id            | Restarts a container in the specified NCC                     | 0..1                                                        |
+-------------------+---------------------------------------------------------------+-------------------------------------------------------------+
|                   |                                                               |                                                             |
| ncp-id            | Restarts a container in the specified NCP                     | 0..max number of NCP per cluster type -1                    |
+-------------------+---------------------------------------------------------------+-------------------------------------------------------------+
|                   |                                                               |                                                             |
| ncf-id            | Restarts a container in the specified NCF                     | 0..max number of NCF per cluster type -1                    |
+-------------------+---------------------------------------------------------------+-------------------------------------------------------------+
|                   |                                                               |                                                             |
| container-name    | Specify the name of the container in the NCE to   restart.    | A container in the NCE. See "show   system" for details.    |
+-------------------+---------------------------------------------------------------+-------------------------------------------------------------+

**Example**
::

	dnRouter# request system container restart ncc 0 routing-engine 
	Warning: Are you sure you want to perform a container restart? (Yes/No) [No]? 
	
	dnRouter# request system container restart ncp 2 forwarding-engine 
	Warning: Are you sure you want to perform a container restart? (Yes/No) [No]? 

.. **Help line:** request system operations

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+