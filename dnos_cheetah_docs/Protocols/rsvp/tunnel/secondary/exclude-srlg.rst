protocols rsvp tunnel secondary exclude-srlg
--------------------------------------------

**Minimum user role:** operator

You can configure a Secondary LSP to avoid interfaces that have the same SRLG as the Primary LSP path.
To set exclude-srlg behavior:

**Command syntax: exclude-srlg [exclude-srlg]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary

**Parameter table**

+--------------+-------------------+------------+---------+
| Parameter    | Description       | Range      | Default |
+==============+===================+============+=========+
| exclude-srlg | exclude srlg mode | | strict   | strict  |
|              |                   | | avoid    |         |
|              |                   | | ignore   |         |
+--------------+-------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# exclude-srlg ignore


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-secondary)# no exclude-srlg

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
