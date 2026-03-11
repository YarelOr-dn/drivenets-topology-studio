protocols rsvp tunnel description
---------------------------------

**Minimum user role:** operator

To enter a description for the tunnel or bypass tunnel:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel
- protocols rsvp tunnel bypass
- protocols rsvp auto-mesh tunnel-template

**Parameter table**

+-------------+----------------------------+------------------+---------+
| Parameter   | Description                | Range            | Default |
+=============+============================+==================+=========+
| description | description for the tunnel | | string         | \-      |
|             |                            | | length 1-255   |         |
+-------------+----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# description MyDescription

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# description MyDescription


**Removing Configuration**

To remove the tunnel's description:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no description

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 9.0     | Command introduced                     |
+---------+----------------------------------------+
| 10.0    | Added support for manual bypass tunnel |
+---------+----------------------------------------+
