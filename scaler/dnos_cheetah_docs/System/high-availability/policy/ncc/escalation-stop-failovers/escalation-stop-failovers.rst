system high-availability policy ncc escalation-stop-failovers
-------------------------------------------------------------

**Minimum user role:** operator

For escalation-stop high-availability violation actions, when a process reaches a high-availability violation, the number of failovers performed in the past failover-period time window is checked.
If the number is smaller than the max-failover, the DNOS high-availability policy escalates to a higher level mitigation (e.g., container reset). Otherwise the process is kept down.

To configure escalation-stop-failovers parameters, enter the escalation-stop-failovers configuration level:

**Command syntax: escalation-stop-failovers**

**Command mode:** config

**Hierarchies**

- system high-availability policy ncc

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# high-availability
    dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# escalation-stop-failovers
    dnRouter(cfg-policy-ncc-es-failovers)#


**Removing Configuration**

To revert all escalation-stop-failovers configuration to default:
::

    dnRouter(cfg-ha-policy-ncc)# no escalation-stop-failovers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
