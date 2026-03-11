services simple-twamp session-sender
------------------------------------

**Minimum user role:** operator

To enter the Simple TWAMP Session-Sender configuration hierarchy:

**Command syntax: session-sender**

**Command mode:** config

**Hierarchies**

- services simple-twamp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-sender
    dnRouter(cfg-srv-stamp-sender)#


**Removing Configuration**

To revert all Simple TWAMP Session-Sender configuration to default:
::

    dnRouter(cfg-srv-stamp)# no session-sender

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
