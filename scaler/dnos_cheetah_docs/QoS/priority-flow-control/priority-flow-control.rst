qos priority-flow-control
-------------------------

**Minimum user role:** operator

Priority Flow Control (PFC; IEEE 802.1Qbb), also referred to as Class-based Flow Control (CBFC) or Per Priority Pause (PPP), is a mechanism that prevents frame loss due to congestion.
PFC is similar to 802.3x Flow Control (pause frames) or Link-level Flow Control (LFC), however, PFC functions on a per class-of-service (CoS) basis.
To enter the global PFC configuration:"

**Command syntax: priority-flow-control**

**Command mode:** config

**Hierarchies**

- qos

**Note**
- The command is applicable to physical interface types.

- You can view the PFC administrative state on an interface using the show interfaces detail command. See "show interfaces detail".

- To view PFC counters use the show PFC counters command. See "show priority-flow-control interfaces counters".

- To view PFC queues use the show PFC queues command. See "show priority-flow-control interfaces queues".

**Example**
::

    dnRouter# configure
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert all PFC settings to their default values:
::

    dnRouter(cfg-qos)# no priority-flow-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
