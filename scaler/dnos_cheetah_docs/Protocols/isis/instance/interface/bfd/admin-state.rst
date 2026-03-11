protocols isis instance interface bfd admin-state
-------------------------------------------------

**Minimum user role:** operator

To enable/disable a BFD session for IS-IS on the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface bfd

**Note**
- If multiple BFD clients are registered to the same BFD session, a single BFD session is established with the strictest session parameters between all clients.

**Parameter table**

+-------------+----------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                          | Range        | Default  |
+=============+======================================================================+==============+==========+
| admin-state | The administrative state of the BFD feature on  the IS-IS interface. | | enabled    | disabled |
|             |                                                                      | | disabled   |          |
+-------------+----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# isis-level level-1-2
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# bfd
    dnRouter(cfg-inst-if-bfd)# admin-state enabled


**Removing Configuration**

To disable BFD on the interface:
::

    dnRouter(cfg-inst-if-bfd)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
