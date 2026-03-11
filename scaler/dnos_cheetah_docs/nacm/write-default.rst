nacm write-default
------------------

**Minimum user role:** admin

Controls whether create, update, or delete access is granted if no appropriate rule is found for a particular write request.

**Command syntax: write-default [write-default]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+---------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter     | Description                                                                      | Range      | Default |
+===============+==================================================================================+============+=========+
| write-default | Controls whether create, update, or delete access is granted if no appropriate   | | permit   | deny    |
|               | rule is found for a particular write request.                                    | | deny     |         |
+---------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# write-default deny


**Removing Configuration**

To revert write-default to the default:
::

    dnRouter(cfg-nacm)# no write-default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
