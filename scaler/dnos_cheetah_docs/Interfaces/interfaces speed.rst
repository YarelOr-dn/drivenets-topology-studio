interfaces speed
----------------

**Minimum user role:** operator

- On NCP-36CD-S and NCP-32CD platforms you can set a 400G interface to support a speed of either 400G or 100G (without breakout).
- On NCP-64X12C-S (NCP-Light) platforms you can set a 10G interface to support a speed of either 10G or 1G (without breakout).

  To set the Ethernet speed of an interface:

**Command syntax: speed [port-speed]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- This command is applicable to physical 400G interfaces on UfiSpace NCP-36CD-S and Accton NCP-32CD platforms that can be set to 100G or to physical 10G interfaces on ufiSpace NCP-64X12C-S platforms that can be set to 1G.

- Port speed and breakout cannot be configured at the same time on an interface.

**Parameter table**

+------------+-------------------------+---------+---------+
| Parameter  | Description             | Range   | Default |
+============+=========================+=========+=========+
| port-speed | The desired port speed. | | 1     | \-      |
|            |                         | | 10    |         |
|            |                         | | 100   |         |
|            |                         | | 400   |         |
+------------+-------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# speed 100

    dnRouter# configure
    dnRouter(cfg)# interfaces ge400-0/0/0 speed 400
    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge10-0/0/0
    dnRouter(cfg-if-ge10-0/0/0)# speed 1

    dnRouter# configure
    dnRouter(cfg)# interfaces ge10-0/0/0 speed 10


**Removing Configuration**

To revert interface speed to its default value:
::

    dnRouter(cfg-if-ge400-0/0/0)# no speed

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
