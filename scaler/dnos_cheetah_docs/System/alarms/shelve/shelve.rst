system alarms shelve
--------------------

**Minimum user role:** operator

To configure alarm shelve policy.

**Command syntax: shelve [shelve]**

**Command mode:** config

**Hierarchies**

- system alarms

**Note**
- The shelve name is a string with a legal length of 1..255 characters.
- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\\"
- When the shelve is deleted all the shelved alarms matching the shelve rule will be un-shelved.

**Parameter table**

+-----------+-------------+------------------+---------+
| Parameter | Description | Range            | Default |
+===========+=============+==================+=========+
| shelve    | shelve      | | string         | \-      |
|           |             | | length 1-255   |         |
+-----------+-------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)#


**Removing Configuration**

To delete the a specific shelve:
::

    dnRouter(cfg-system-alarms)# no shelve my_shelve

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
