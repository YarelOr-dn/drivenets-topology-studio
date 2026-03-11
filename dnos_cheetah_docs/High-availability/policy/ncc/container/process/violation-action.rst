system high-availability policy ncc container process violation-action
----------------------------------------------------------------------

**Minimum user role:** operator

Defines the high-availablity action expected to take place upon process HA violation.

Possible actions:
- hold-down – Process is stopped, system continues to run. SYSTEM_PROCESS_HELD_DOWN syslog is expected
- always-escalate - Escalate violation to parent entity, and declare failure at parent container level, which will reset the parent container (default, similar to 13.3 today). SYSTEM_PROCESS_HA_VIOLATION syslog is expected.

**Command syntax: violation-action [violation-action]**

**Command mode:** config

**Hierarchies**

- high-availability policy ncc container process

**Parameter table:**

+------------------+--------------------------------+------------------------------------------------------------+
| Parameter        | Values                         | Default value                                              |
+==================+================================+============================================================+
| violation-action | hold-down , always-escalate    |  See DNOS High-Availablity guide for value per process     |
+------------------+--------------------------------+------------------------------------------------------------+


**Note**
 - Reconfiguration will lead to mitigations counter and mitigation-period-timer reset

 - Reconfiguration will not change current process state (i.e bring it up if process is down)


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# container routing-engine
    dnRouter(cfg-policy-ncc-container)# process routing:pimd
    dnRouter(cfg-ncc-container-process)# violation-action hold-down



**Removing Configuration**

To revert failure-period configuration to default value:
::

	dnRouter(cfg-ncc-container-process)# no violation-action


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
