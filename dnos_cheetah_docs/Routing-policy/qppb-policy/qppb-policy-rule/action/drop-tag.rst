routing-policy qppb-policy rule action drop-tag
-----------------------------------------------

**Minimum user role:** operator

Configures the drop-tag that shall be set on the packets that match the rule. 
The drop-tag is mandatory when configuring the qos-tag.

To configure the drop-tag:

**Command syntax: drop-tag [drop-tag]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule action

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------+---------------------+------------+---------+
| Parameter | Description         | Range      | Default |
+===========+=====================+============+=========+
| drop-tag  | Drop priority color | | green    | \-      |
|           |                     | | yellow   |         |
+-----------+---------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action) drop-tag yellow
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action)


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action)# no drop-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
