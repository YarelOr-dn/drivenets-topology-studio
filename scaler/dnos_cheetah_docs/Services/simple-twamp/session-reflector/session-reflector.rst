services simple-twamp session-reflector
---------------------------------------

**Minimum user role:** operator

To enter the Simple TWAMP Session-Reflector configuration hierarchy:

**Command syntax: session-reflector**

**Command mode:** config

**Hierarchies**

- services simple-twamp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-reflector
    dnRouter(cfg-srv-stamp-reflector)#


**Removing Configuration**

To revert all Simple TWAMP Session-Reflector configuration to default:
::

    dnRouter(cfg-srv-stamp)# no session-reflector

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
