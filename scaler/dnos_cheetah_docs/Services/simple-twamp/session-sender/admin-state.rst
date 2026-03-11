services simple-twamp session-sender admin-state
------------------------------------------------

**Minimum user role:** operator

To enable or disable the Simple TWAMP Session-Sender:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services simple-twamp session-sender

**Parameter table**

+-------------+-------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                 | Range        | Default  |
+=============+=============================================================+==============+==========+
| admin-state | The administrative state of the Simple TWAMP Session-Sender | | enabled    | disabled |
|             |                                                             | | disabled   |          |
+-------------+-------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-srv)# simple-twamp
    dnRouter(cfg-srv-stamp)# session-sender
    dnRouter(cfg-srv-stamp-sender)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-srv-stamp-sender)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
