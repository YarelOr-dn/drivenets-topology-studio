protocols isis instance description
-----------------------------------

**Minimum user role:** operator

When configuring multiple IS-IS instances, it may be helpful to add a description for each configured instance.

To configure a description for the IS-IS instance:


**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| description | Add a description for the IS-IS instance.                                        | | string         | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do    | | length 1-255   |         |
|             | not use quotation marks, do not use spaces. For example:                         |                  |         |
|             | ... description "My long description"                                            |                  |         |
|             | ... description My_long_description                                              |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# description "IS-IS metro region 1"


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-protocols-isis-inst)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
