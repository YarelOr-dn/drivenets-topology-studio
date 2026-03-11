protocols rsvp auto-bypass primary exclude-srlg
-----------------------------------------------

**Minimum user role:** operator

You can configure a bypass-tunnel to avoid interfaces that have the same SRLG-ID as the main path (see "mpls traffic-engineering interface srlg-group").
There are 3 exclusion modes, each has a slightly different effect:

- Strict - a path will not be accepted if it traverses in a link with the same SRLG-ID

- Avoid - the path with the least number of links that have SRLG conflict will be selected

- Ignore - SRLG will be ignored for CSPF path calculation

To set this behavior:

**Command syntax: exclude-srlg [exclude-srlg]**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass primary
- protocols rsvp tunnel bypass primary

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
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# primary
    dnRouter(cfg-rsvp-bypass-tunnel-primary)# exclude-srlg ignore

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# primary
    dnRouter(cfg-rsvp-auto-bypass-primary)# exclude-srlg ignore


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-auto-bypass-primary)# no exclude-srlg

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
