services simple-twamp session-reflector reflector-port
------------------------------------------------------

**Minimum user role:** operator

To configure the local port for the Simple TWAMP Session-Reflector:

**Command syntax: reflector-port [reflector-port]**

**Command mode:** config

**Hierarchies**

- services simple-twamp session-reflector

**Parameter table**

+----------------+--------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                  | Range   | Default |
+================+==============================================================+=========+=========+
| reflector-port | The source port number of the local STAMP Session-Reflector. | 1-65535 | 862     |
+----------------+--------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-reflector
    dnRouter(cfg-srv-stamp-reflector)# reflector-port 863


**Removing Configuration**

To revert reflector-port to default:
::

    dnRouter(cfg-srv-stamp-reflector)# no reflector-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
