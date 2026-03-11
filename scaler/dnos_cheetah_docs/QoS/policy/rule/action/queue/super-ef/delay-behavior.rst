qos policy rule action queue forwarding-class super-ef delay-behavior
---------------------------------------------------------------------

**Minimum user role:** operator

To configure the delay behavior of a specific queue:

**Command syntax: delay-behavior [delay-behavior]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class super-ef

**Parameter table**

+----------------+----------------------+---------------+---------+
| Parameter      | Description          | Range         | Default |
+================+======================+===============+=========+
| delay-behavior | queue delay behavior | | low-delay   | \-      |
|                |                      | | normal      |         |
+----------------+----------------------+---------------+---------+

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
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# delay-behavior low-delay


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no delay-behavior

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
