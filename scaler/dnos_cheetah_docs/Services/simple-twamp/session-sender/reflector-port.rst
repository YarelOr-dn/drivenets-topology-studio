services simple-twamp session-sender reflector-port
---------------------------------------------------

**Minimum user role:** operator

To configure the remote port of the target Simple TWAMP Session-Reflector:

**Command syntax: reflector-port [reflector-port]**

**Command mode:** config

**Hierarchies**

- services simple-twamp session-sender

**Parameter table**

+----------------+-----------------------------------------------------------------------------+---------+---------+
| Parameter      | Description                                                                 | Range   | Default |
+================+=============================================================================+=========+=========+
| reflector-port | The destination UDP port number towards the remote STAMP Session-Reflector. | 1-65535 | 862     |
+----------------+-----------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-sender
    dnRouter(cfg-srv-stamp-sender)# reflector-port 863


**Removing Configuration**

To revert reflector-port to default:
::

    dnRouter(cfg-srv-stamp-sender)# no reflector-port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
