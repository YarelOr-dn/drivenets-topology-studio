routing-policy qppb-policy rule actions drop-tag
------------------------------------------------

**Minimum user role:** operator

To Configure the drop-tag that shall be set on the packets that match the rule.  Drop-tag is mandatory when configuring qos-tag.

To create a set action:

**Command syntax: drop-tag [drop-tag]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule actions

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------+---------------------+----------+---------+
| Parameter | Description         | Range    | Default |
+===========+=====================+==========+=========+
| drop-tag  | Drop priority color | green    | \-      |
|           |                     | yellow   |         |
+-----------+---------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# actions
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions) drop-tag yellow
    dnRouter(cfg-qppb-policy-PL-1-rule-10-actions)


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action-set)# no drop-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
