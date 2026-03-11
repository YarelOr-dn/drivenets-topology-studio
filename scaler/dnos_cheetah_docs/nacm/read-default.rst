nacm read-default
-----------------

**Minimum user role:** admin

Controls whether read access is granted if no appropriate rule is found for a particular read request.

**Command syntax: read-default [read-default]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter    | Description                                                                      | Range      | Default |
+==============+==================================================================================+============+=========+
| read-default | Controls whether read access is granted if no appropriate rule is found for a    | | permit   | permit  |
|              | particular read request.                                                         | | deny     |         |
+--------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# read-default deny


**Removing Configuration**

To revert read-default to the default value:
::

    dnRouter(cfg-nacm)# no read-default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
