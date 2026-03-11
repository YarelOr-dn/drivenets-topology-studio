qos policy rule action queue
----------------------------

**Minimum user role:** operator

To configure the queue for the matched traffic class.

**Command syntax: queue**

**Command mode:** config

**Hierarchies**

- qos policy rule action

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action)# no queue

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
