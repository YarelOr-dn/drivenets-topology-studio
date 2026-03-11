system high-availability policy ncc escalation-stop-failovers failover-period
-----------------------------------------------------------------------------

**Minimum user role:** operator

To configure the failover time period that DNOS allows max-failovers, for the escalation-stop logic:

**Command syntax: failover-period [failover-period]**

**Command mode:** config

**Hierarchies**

- system high-availability policy ncc escalation-stop-failovers

**Note**

- for max-failovers = 0 failover-period has no effect.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| failover-period | time window in minutes, for which NCC failovers are counted for escalate-stop    | 1-65535 | 30      |
|                 | decision                                                                         |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# high-availability
    dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# escalation-stop-failovers
    dnRouter(cfg-policy-ncc-es-failovers)# failover-period 10


**Removing Configuration**

To revert failover-period to default:
::

    dnRouter(cfg-policy-ncc-es-failovers)# no failover-period

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
