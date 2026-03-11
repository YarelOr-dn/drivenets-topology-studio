system alarms shelve description
--------------------------------

**Minimum user role:** operator

To add an optional description of the shelve policy.

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- system alarms shelve

**Note**

- The legal string length is 1..255 characters.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter   | Description                                                                      | Range | Default |
+=============+==================================================================================+=======+=========+
| description | Add a description for the Alarms Shelve Policy.                                  | \-    | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do    |       |         |
|             | not use quotation marks, do not use spaces. For example:                         |       |         |
|             | ... description "My long description"                                            |       |         |
|             | ... description My_long_description                                              |       |         |
+-------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# shelve my_shelve
    dnRouter(cfg-system-alarms-shelve)# description My-description
    dnRouter(cfg-system-alarms-shelve)#


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-system-alarms-shelve)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
