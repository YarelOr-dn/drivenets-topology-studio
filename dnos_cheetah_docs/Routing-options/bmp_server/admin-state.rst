routing-options bmp server admin-state
--------------------------------------

**Minimum user role:** operator

To enable the BMP server to which the BGP neighbor tables information will be sent.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+-------------+------------------------+--------------+----------+
| Parameter   | Description            | Range        | Default  |
+=============+========================+==============+==========+
| admin-state | bmp server admin-state | | enabled    | disabled |
|             |                        | | disabled   |          |
+-------------+------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# admin-state enabled


**Removing Configuration**

To return the admin-state to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
