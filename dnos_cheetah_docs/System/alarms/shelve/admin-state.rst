system alarms shelve admin-state
--------------------------------

**Minimum user role:** operator

Shelve 'admin-state' enabled/disabled switch is provided to enable or disable shelve policy.
When this switch is set to 'enabled', all alarms matching the one of the rules under the shelve will be shelved.
When this switch is set to 'disabled', all the alarms shelved by this shelve will be will be un-shelved.
Shelve disable/enable doesn't affect the history records, but in case an active alarm will be shelved, once it will be cleared and move to the alarm history the shelved entry will be updated in the history.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system alarms shelve

**Parameter table**

+-------------+-----------------------------------------+--------------+----------+
| Parameter   | Description                             | Range        | Default  |
+=============+=========================================+==============+==========+
| admin-state | DNOS Alarms admin-state enable/disabled | | enabled    | disabled |
|             |                                         | | disabled   |          |
+-------------+-----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)# admin-state enabled
    dnRouter(cfg-system-alarms-shelve)#


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-alarms-shelve)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
