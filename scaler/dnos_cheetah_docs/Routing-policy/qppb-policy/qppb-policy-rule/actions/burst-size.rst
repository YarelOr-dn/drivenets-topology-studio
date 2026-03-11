routing-policy qppb-policy rule actions burst-size
--------------------------------------------------

**Minimum user role:** operator

Set the burst-size for the traffic matched by the rule.


To create a set action:

**Command syntax: burst-size [burst-size] [units]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+------------+-------------------------------------------------+------------+---------+
| Parameter  | Description                                     | Range      | Default |
+------------+-------------------------------------------------+------------+---------+
| burst-size | Committed burst size in kilo bytes (1000 bytes) | 50..255000 | 200     |
+------------+-------------------------------------------------+------------+---------+
| units      |                                                 | kbytes     | kbytes  |
|            |                                                 | mbytes     |         |
+------------+-------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) burst-size 200 mbytes
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)# no burst-size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
