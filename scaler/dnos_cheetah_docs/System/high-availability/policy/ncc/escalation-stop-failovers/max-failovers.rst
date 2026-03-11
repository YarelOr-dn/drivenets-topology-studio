system high-availability policy ncc escalation-stop-failovers max-failovers
---------------------------------------------------------------------------

**Minimum user role:** operator

To configure the maximum amount of allowed NCC failovers in a failover period:

**Command syntax: max-failovers [max-failovers]**

**Command mode:** config

**Hierarchies**

- system high-availability policy ncc escalation-stop-failovers

**Note**

- Any user operation that causes an NCC to restart or switchover will result in resetting the failover counter.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                      | Range | Default |
+===============+==================================================================================+=======+=========+
| max-failovers | maximum number of allowed failovers in a failover period. When number of         | 0-255 | 2       |
|               | failover reach maximum value, escalate-stop flow will result in stopping the     |       |         |
|               | failed process                                                                   |       |         |
+---------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# high-availability
    dnRouter(cfg-system-ha)# policy
    dnRouter(cfg-system-ha-policy)# ncc
    dnRouter(cfg-ha-policy-ncc)# escalation-stop-failovers
    dnRouter(cfg-policy-ncc-es-failovers)#  max-failovers 1


**Removing Configuration**

To revert max-failovers to default:
::

    dnRouter(cfg-policy-ncc-es-failovers)# no max-failovers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
