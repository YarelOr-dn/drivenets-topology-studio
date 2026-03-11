protocols isis instance overload on-startup admin-state
-------------------------------------------------------

**Minimum user role:** operator

Use the command to enable or disable the IS-IS overload behavior upon system start. Once set, the default behavior for the system is to advertise the overload-bit for the configured interval period. The overload-bit signals other routers not to use it as an intermediate hop in their SPF calculations.

To set the IS-IS overload behavior on startup:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance overload on-startup

**Parameter table**

+-------------+--------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                  | Range        | Default  |
+=============+==============================================================+==============+==========+
| admin-state | Administratively sets the IS-IS overload behavior on startup | | enabled    | disabled |
|             |                                                              | | disabled   |          |
+-------------+--------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# overload on-startup
    dnRouter(cfg-isis-inst-overload)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-overload)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
