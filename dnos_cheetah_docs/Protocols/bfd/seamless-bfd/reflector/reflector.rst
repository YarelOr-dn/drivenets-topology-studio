protocols bfd seamless-bfd reflector
------------------------------------

**Minimum user role:** operator

Configure a seamless BFD Reflector.

**Command syntax: reflector [reflector-name]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd

**Parameter table**

+----------------+---------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                         | Range            | Default |
+================+=====================================================================+==================+=========+
| reflector-name | The name of the reflector -- used to address the specific reflector | | string         | \-      |
|                |                                                                     | | length 1-255   |         |
+----------------+---------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To remove the reflector from the system.
::

    dnRouter(cfg-protocols-bfd-seamless)# no reflector

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
