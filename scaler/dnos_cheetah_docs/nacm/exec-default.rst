nacm exec-default
-----------------

**Minimum user role:** admin

Controls whether exec access is granted if no appropriate rule is found for a particular protocol operation request. To configure the exec access:

**Command syntax: exec-default [exec-default]**

**Command mode:** config

**Hierarchies**

- nacm

**Parameter table**

+--------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter    | Description                                                                      | Range      | Default |
+==============+==================================================================================+============+=========+
| exec-default | Controls whether exec access is granted if no appropriate rule is found for a    | | permit   | deny    |
|              | particular protocol operation request.                                           | | deny     |         |
+--------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# nacm
    dnRouter(cfg-nacm)# exec-default deny


**Removing Configuration**

To revert exec-default:
::

    dnRouter(cfg-nacm)# no exec-default

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
