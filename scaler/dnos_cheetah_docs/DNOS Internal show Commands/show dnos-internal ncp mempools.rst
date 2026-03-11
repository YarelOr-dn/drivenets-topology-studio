show dnos-internal ncp mempools
-------------------------------

**Minimum user role:** viewer

To display statistics on memory pools that are used in wb-agent:

**Command syntax:show dnos-internal ncp [ncp-id] mempools**

**Command mode:** operation

**Parameter table**

+---------------+-------------------------------------------------------+----------------------------+
|               |                                                       |                            |
| Parameter     | Description                                           | Range                      |
+===============+=======================================================+============================+
|               |                                                       |                            |
| ncp-id        | Display the information for the specified NCP only    | 0..cluster type maximum -1 |
|               |                                                       |                            |
|               |                                                       | \* all NCPs                |
+---------------+-------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter#  show dnos-internal ncp * mempools

	NCP 0 Table: /mempools

	| name                      | size    | allocated_objects   | id   | n_allocations   | n_failed_allocations   | n_releases   | n_allocations-rate   | n_releases-rate   |
	|---------------------------+---------+---------------------+------+-----------------+------------------------+--------------+----------------------+-------------------|
	| em_critical_ring_0        | 1024    | 0                   | 0    | 0               | 0                      | 0            | 0                    | 0                 |
	| em_critical_ring_1        | 1024    | 0                   | 1    | 0               | 0                      | 0            | 0                    | 0                 |
	| em_critical_ring_2        | 1024    | 0                   | 2    | 0               | 0                      | 0            | 0                    | 0                 |
	| em_config_ring            | 1024    | 0                   | 3    | 82              | 0                      | 82           | 0                    | 0                 |
	| rsm_1_oper__mp            | 511     | 41                  | 4    | 41              | 0                      | 0            | 0                    | 0                 |
	| rsm_1_c0_cfg_mp           | 511     | 41                  | 5    | 41              | 0                      | 0            | 0                    | 0                 |
	| rsm_1_c1_cfg_mp           | 511     | 42                  | 6    | 42              | 0                      | 0            | 0                    | 0                 |
	| wbox_interface_list_oper  | 2048    | 40                  | 7    | 40              | 0                      | 0            | 0                    | 0                 |
	| acl_rules                 | 250000  | 0                   | 8    | 0               | 0                      | 0            | 0                    | 0                 |
	| acl_rule_ids_pool         | 1000000 | 0                   | 9    | 0               | 0                      | 0            | 0                    | 0                 |
	| acl_ordered_rules         | 500000  | 0                   | 10   | 0               | 0                      | 0            | 0                    | 0                 |
	| acl_policy_rules_0        | 500000  | 0                   | 11   | 0               | 0                      | 0            | 0                    | 0                 |
	| acl_attached_interfaces_0 | 30000   | 0                   | 12   | 0               | 0                      | 0            | 0                    | 0                 |
	| ranges_pool_0             | 48      | 0                   | 13   | 0               | 0                      | 0            | 0                    | 0                 |
	| resources_pool_0          | 216000  | 0                   | 14   | 0               | 0                      | 0            | 0                    | 0                 |

	...

.. **Help line:** Displays stats on memory pools that are used in wb-agent

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+
