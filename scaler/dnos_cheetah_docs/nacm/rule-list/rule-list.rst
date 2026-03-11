nacm rule-list
--------------

**Minimum user role:** admin

Processes all rule-list entries, in the order they appear in the configuration. If a rule-list's 'group' leaf-list does not match any of the user's groups, it will proceed to the next rule-list entry. For each rule-list entry found, all rules are processed, in order, until a rule that matches the requested access operation is found.

**Command syntax: rule-list [rule-list]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+-----------+-------------------------------------------+-------------------------+---------+
| Parameter | Description                               | Range                   | Default |
+===========+===========================================+=========================+=========+
| rule-list | Arbitrary name assigned to the rule-list. | | string                | \-      |
|           |                                           | | length 1-4294967295   |         |
+-----------+-------------------------------------------+-------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# rule-list <rule-list-name>


**Removing Configuration**

To revert the rule-list to the default:
::

    dnRouter(cfg-nacm)# no rule-list <rule-list-name>

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
