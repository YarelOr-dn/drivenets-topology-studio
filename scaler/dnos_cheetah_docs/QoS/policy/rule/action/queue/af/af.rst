qos policy rule action queue forwarding-class af
------------------------------------------------

**Minimum user role:** operator

To configure the af queue forwarding-class for the matched traffic:

**Command syntax: forwarding-class af**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue

**Note**

- Up to 6 af forwarding-class queues can be used, with a total of 8 queues.

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


**Removing Configuration**

To remove the queue configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue)# no af

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
