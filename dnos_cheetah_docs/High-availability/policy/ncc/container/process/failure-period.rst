system high-availability policy ncc container process failure-period
--------------------------------------------------------------------

**Minimum user role:** operator

Defines the time period (in minutes) process failures are accumalated in order to tigger process HA violation.
If the number of process failures in the last “failure-period” minutes exceed max-failures, process HA violation is triggered.
For max-failures = 0, the “failure-period” has no real effect.
To configure the failure period:

**Command syntax: failure-period [failure-period]**

**Command mode:** config

**Hierarchies**

- high-availability policy ncc container process

**Parameter table:**

+----------------+---------------------+------------------------------------------------------------+
| Parameter      | Values              | Default value                                              |
+================+=====================+============================================================+
| failure-period | 1..65535            |  See DNOS High-Availablity guide for value per process     |
+----------------+---------------------+------------------------------------------------------------+


**Note**
 - Reconfiguration will lead to mitigations counter and mitigation-period-timer reset

 - Reconfiguration will not change the current process state (i.e bring it up if the process is down).


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# high-availability
	dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# container routing-engine
    dnRouter(cfg-policy-ncc-container)# process routing:pimd
    dnRouter(cfg-ncc-container-process)# failure-period 5



**Removing Configuration**

To revert failure-period configuration to default value:
::

	dnRouter(cfg-ncc-container-process)# no failure-period


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
