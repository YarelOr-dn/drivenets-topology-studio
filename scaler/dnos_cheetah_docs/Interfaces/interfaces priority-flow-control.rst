interfaces priority-flow-control
--------------------------------

**Minimum user role:** operator

Priority Flow Control (PFC; IEEE 802.1Qbb), also referred to as Class-based Flow Control (CBFC) or Per Priority Pause (PPP), is a mechanism that prevents frame loss due to congestion.
PFC is similar to 802.3x Flow Control (pause frames) or Link-level Flow Control (LFC), however, PFC functions on a per traffic class basis.
To enter the PFC configuration on an interface:"

**Command syntax: priority-flow-control**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**
- The command is applicable to physical interface types.

- You can view the PFC administrative state on an interface using the show interfaces detail command. See "show interfaces detail".

- To view PFC counters use the show PFC counters command. See "show priority-flow-control interfaces counters".

- To view PFC queues use the show PFC queues command. See "show priority-flow-control interfaces queues".

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# priority-flow-control
    dnRouter(cfg-if-ge100-0/0/0-pfc)#


**Removing Configuration**

To revert all PFC settings to their default values:
::

    dnRouter(cfg-if-ge100-0/0/0)# no priority-flow-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
