services simple-twamp session-reflector dscp-value
--------------------------------------------------

**Minimum user role:** operator

To set the DSCP value for reflected packets:

**Command syntax: dscp-value [class-of-service]**

**Command mode:** config

**Hierarchies**

- services simple-twamp session-reflector

**Parameter table**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                                      | Range | Default |
+==================+==================================================================================+=======+=========+
| class-of-service | The DSCP value for reflected STAMP packets if dscp-handling-mode is set to       | 0-56  | 0       |
|                  | use-configured-value.                                                            |       |         |
+------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-reflector
    dnRouter(cfg-srv-stamp-reflector)# dscp-value 0


**Removing Configuration**

To return the DSCP value to default:
::

    dnRouter(cfg-srv-stamp-reflector)# no dscp-value

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
