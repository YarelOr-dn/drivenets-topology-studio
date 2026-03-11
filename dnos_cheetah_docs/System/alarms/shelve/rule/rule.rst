system alarms shelve rule
-------------------------

**Minimum user role:** operator

You can create multiple rules per policy.
The rule values should be in the range of [1..100].

**Command syntax: rule [rule]**

**Command mode:** config

**Hierarchies**

- system alarms shelve

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| rule      | the unique entry id. lower id means higher priority match Each entry defines the | 1-100 | \-      |
|           | criteria for shelving alarms. Criteria are ANDed.  If no criteria are specified, |       |         |
|           | all alarms will be shelved.                                                      |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)# rule 8
    dnRouter(cfg-alarms-shelve-rule)#


**Removing Configuration**

To delete the rule:
::

    dnRouter(cfg-alarms-shelve-rule)# no rule 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
