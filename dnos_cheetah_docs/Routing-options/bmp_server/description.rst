routing-options bmp server description
--------------------------------------

**Minimum user role:** operator

To set a description for the BMP server.

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+-------------+------------------------+------------------+---------+
| Parameter   | Description            | Range            | Default |
+=============+========================+==================+=========+
| description | bmp server description | | string         | \-      |
|             |                        | | length 1-255   |         |
+-------------+------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# description "bmp server running on openBMP"


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-routing-option-bmp)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
