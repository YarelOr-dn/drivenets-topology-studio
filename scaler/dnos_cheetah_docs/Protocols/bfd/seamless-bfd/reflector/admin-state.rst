protocols bfd seamless-bfd reflector admin-state
------------------------------------------------

**Minimum user role:** operator

To enable or disable the Seamless BFD Reflector

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bfd seamless-bfd reflector

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | set whether bfd protection is in use | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# seamless-bfd
    dnRouter(cfg-protocols-bfd-seamless)# reflector reflector1
    dnRouter(cfg-bfd-seamless-reflector)# admin-state enabled
    dnRouter(cfg-bfd-seamless-reflector)#


**Removing Configuration**

To restore the admin-state to its default of disabled.
::

    dnRouter(cfg-bfd-seamless-reflector)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
