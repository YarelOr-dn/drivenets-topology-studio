interfaces tracking-group action
--------------------------------

**Minimum user role:** operator

Configure this interface to track one of the defined tracking groups. According to the state of
the objects in the tracking group (for example all objects have failed) then the action defined here (example: laser off)
will be applied to this interface. When the objects in the tracking group recover then the reverse action (example: laser on)
will be implemented.

**Command syntax: tracking-group [if-tracking-group-name] action [action]**

**Command mode:** config

**Hierarchies**

- interfaces

**Parameter table**

+------------------------+-------------------------------------------------------------------+-----------------+-----------+
| Parameter              | Description                                                       | Range           | Default   |
+========================+===================================================================+=================+===========+
| if-tracking-group-name | The name of the tracking group                                    | | string        | \-        |
|                        |                                                                   | | length 1-63   |           |
+------------------------+-------------------------------------------------------------------+-----------------+-----------+
| action                 | Action to be performed when the tracked group conditions are met. | laser-off       | laser-off |
+------------------------+-------------------------------------------------------------------+-----------------+-----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# tracking-group tracking-group1 action laser-off
    dnRouter(cfg-if-ge400-0/0/0)#


**Removing Configuration**

::

    dnRouter(cfg-if-ge400-0/0/0)# no tracking-group

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
