protocols bfd seamless-bfd reflector description
------------------------------------------------

**Minimum user role:** operator

To add an optional description to the Seamless BFD Reflector

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd reflector

**Parameter table**

+-------------+-----------------------+------------------+---------+
| Parameter   | Description           | Range            | Default |
+=============+=======================+==================+=========+
| description | reflector description | | string         | \-      |
|             |                       | | length 1-255   |         |
+-------------+-----------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)# description "Seamless BFD Reflector"
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To remove description
::

    dnRouter(cfg-bfd-seamless-reflector)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
