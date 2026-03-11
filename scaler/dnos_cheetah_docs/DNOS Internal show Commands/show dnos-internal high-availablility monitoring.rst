show dnos-internal high-availablility monitoring
------------------------------------------------

**Minimum user role:** viewer

To display high-availability information for DNOS processes:

**Command syntax: show dnos-internal high-availablility monitoring** {ncc [ncc-id] | ncp [ncp-id] | ncf [ncf-id]} container [container-name] process [process-name]

**Command mode:** operation

**Parameter table**

+-------------------+----------------------------------------------------------------+--------------------------------------------------------+
|                   |                                                                |                                                        |
| Parameter         | Description                                                    | Range                                                  |
+===================+================================================================+========================================================+
|                   |                                                                |                                                        |
| ncc-id            | Filter the displayed information to the specified NCC          | 0..1                                                   |
+-------------------+----------------------------------------------------------------+--------------------------------------------------------+
|                   |                                                                |                                                        |
| ncp-id            | Filter the displayed information to the specified NCP          | 0..255                                                 |
+-------------------+----------------------------------------------------------------+--------------------------------------------------------+
|                   |                                                                |                                                        |
| ncf-id            | Filter the displayed information to the specified NCF          | 0..[max number of NCFs for the cluster type -1]        |
+-------------------+----------------------------------------------------------------+--------------------------------------------------------+
|                   |                                                                |                                                        |
| container-name    | Filter the displayed information to the specified container    | A container name from the process list for the node    |
+-------------------+----------------------------------------------------------------+--------------------------------------------------------+
|                   |                                                                |                                                        |
| process-name      | Filter the displayed information to the specified process      | A process from the process list                        |
+-------------------+----------------------------------------------------------------+--------------------------------------------------------+

**Example**
::

    
    dnRouter# show dnos-internal high-availablility monitoring

    Policy regular max-reset 2 in 5 minutes
    Policy essential max-reset 2 in 5 minutes
    Policy critical max-reset 1
    Policy max-switchover 2 in 5 minutes

    Containers:
    
	| Type | Id | Container         | State  | HA policy       |
	|------+----+-------------------+--------+-----------------+
	| NCC  | 0  | routing-engine    | up     | critical        |
	| NCC  | 0  | management-engine | up     | critical        |
	| NCP  | 0  | forwarding-engine | up     | critical        |
	| NCF  | 0  | ncc-selector      | up     | critical        |
    ...

    Processes:

	| Type | Id | Container         | Process              | State  | HA policy       | Timer value [hello/dead]  | Last Hello |
	|------+----+-------------------+----------------------+--------+-----------------+---------------------------+------------+
	| NCC  | 0  | routing-engine    | re_interface_manager | up     | critical        | 10/30sec                  | 3sec       |
	| NCC  | 0  | routing-engine    | bgpd                 | up     | essential       | 10/30sec                  | 3sec       |
	| NCC  | 0  | routing-engine    | rsvpd                | up     | essential       | 10/30sec                  | 3sec       |
	| NCC  | 0  | management-engine | ntpd                 | up     | restartable     | 10/30sec                  | 3sec       |
	| NCC  | 0  | management-engine | transaction_manager  | up     | critical        | 10/30sec                  | 3sec       |
	| NCP  | 0  | forwarding-engine | wb_agent             | up     | essential       | 10/30sec                  | 3sec       |
	| NCF  | 0  | ncc-selector      | selector             | up     | regular         | 10/30sec                  | 3sec       |
	...

	dnRouter# show dnos-internal high-availablility monitoring process bgpd

    Policy regular max-reset 2 in 5 minutes
    Policy essential max-reset 2 in 5 minutes
    Policy critical max-reset 1
    Policy max-switchover 2 in 5 minutes

	| Type | Id | Container         | Process name         | State  | HA policy       | Timer value [hello/dead]  | Last Hello |
	|------+----+-------------------+----------------------+--------+-----------------+---------------------------+------------+
	| NCC  | 0  | routing-engine    | bgpd                 | up     | critical        | 10/30sec                  | 3sec       |
	| NCC  | 1  | routing-engine    | bgpd                 | Down   | critical        | 10/30sec                  |            |
	

.. **Help line:** Display DNOS processes high availability

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.5        | Command introduced    |
+-------------+-----------------------+


