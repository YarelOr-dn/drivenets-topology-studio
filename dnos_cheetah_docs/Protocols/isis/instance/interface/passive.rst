protocols isis instance interface passive
-----------------------------------------

**Minimum user role:** operator

Setting an interface to passive mode, instructs IS-IS to only advertise its IP address in the link-state PDUs without running the IS-IS protocol. The interface will not send or receive IS-IS packets.

To set the interface to passive mode:

**Command syntax: passive [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Note**

- Loopback interfaces configured with IS-IS are automatically passive by default and cannot be set to active.

- Passive interfaces receive a metric value of 0 by default.

**Parameter table**

+-------------+-----------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                           | Range        | Default  |
+=============+=======================================================================+==============+==========+
| admin-state | The administrative state of the passive mode for the IS-IS interface. | | enabled    | disabled |
|             |                                                                       | | disabled   |          |
+-------------+-----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# passive enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-isis-inst-if)# no passive

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Command removed      |
+---------+----------------------+
| 10.0    | Command reintroduced |
+---------+----------------------+
