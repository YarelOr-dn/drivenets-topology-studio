tracking-policy tracking-group
------------------------------

**Minimum user role:** operator

To configure a tracking group

**Command syntax: tracking-group [tracking-group-name]**

**Command mode:** config

**Hierarchies**

- tracking-policy

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+---------------------+--------------------------------+-----------------+---------+
| Parameter           | Description                    | Range           | Default |
+=====================+================================+=================+=========+
| tracking-group-name | The name of the tracking group | | string        | \-      |
|                     |                                | | length 1-63   |         |
+---------------------+--------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# tracking-policy
    dnRouter(cfg-trkpl)# tracking-group group1
    dnRouter(cfg-trkpl-trkgrp)#


**Removing Configuration**

To remove the specified tracking group:
::

    dnRouter(cfg-trkpl)# no tracking-group group1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
