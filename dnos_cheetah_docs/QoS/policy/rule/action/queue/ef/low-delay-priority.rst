qos policy rule action queue forwarding-class ef low-delay-priority
-------------------------------------------------------------------

**Minimum user role:** operator

To configure the low-delay-priority of a specific queue:

**Command syntax: low-delay-priority [low-delay-priority]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class ef

**Parameter table**

+--------------------+--------------------------+----------+---------+
| Parameter          | Description              | Range    | Default |
+====================+==========================+==========+=========+
| low-delay-priority | queue low-delay-priority | | high   | \-      |
|                    |                          | | low    |         |
+--------------------+--------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# af
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# low-delay-priority high


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no low-delay-priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
