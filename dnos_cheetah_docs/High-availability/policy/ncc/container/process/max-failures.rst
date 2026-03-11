system high-availability policy ncc container process max-failures
------------------------------------------------------------------

**Minimum user role:** operator

Defines the amount of failures a process may have in a given “failure-period” before declaring process HA violation.
Each allowed failure will be handled by the process defined mitigation (process restart).
For 0 value, the process will have an HA violation upon first failure.
To configure max-failures:

**Command syntax: max-familures [max-failures]**

**Command mode:** config

**Hierarchies**

- high-availability policy ncc container process

**Parameter table:**

+----------------+---------------------+------------------------------------------------------------+
| Parameter      | Values              | Default value                                              |
+================+=====================+============================================================+
| max-failures   | 0..65535            |  See DNOS High-Availablity guide for value per process     |
+----------------+---------------------+------------------------------------------------------------+


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
    dnRouter(cfg-ncc-container-process)# max-familiars 3



**Removing Configuration**

To revert max-familiars configuration to default value:
::

	dnRouter(cfg-ncc-container-process)# no max-familiars


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
