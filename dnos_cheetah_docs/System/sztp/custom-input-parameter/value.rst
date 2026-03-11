system sztp custom-input-parameter value
----------------------------------------

**Minimum user role:** admin

To configure the value of the custom parameter

**Command syntax: value [value]**

**Command mode:** config

**Hierarchies**

- system sztp custom-input-parameter

**Parameter table**

+-----------+-------------------------------+------------------+---------+
| Parameter | Description                   | Range            | Default |
+===========+===============================+==================+=========+
| value     | Value of the custom parameter | | string         | \-      |
|           |                               | | length 0-255   |         |
+-----------+-------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# custom-input-parameter my-parameter
    dnRouter(cfg-system-sztp-custin)# value "hello"


**Removing Configuration**

To remove value to default:
::

    dnRouter(cfg-system-sztp-custin)# no value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
