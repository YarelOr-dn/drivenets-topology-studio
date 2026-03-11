protocols rsvp tunnel secondary disjoint-preference
---------------------------------------------------

**Minimum user role:** operator

Sets a disjoint constraint preference for establishing a Secondary LSP.
By default, requires a strictly disjoint path excluding any link and node used in Primary LSP path. If no path is found, no Secondary LSP is provided.
When “avoid” is set, the Secondary LSP avoids utilizing links and nodes used in the primary path as much as possible, but if no other alternative secondary path can pass through them. This increases finding a path for secondary.
To set a disjoint constraint preference:

**Command syntax: disjoint-preference [preference]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary

**Parameter table**

+------------+----------------------------------------------------------------------------------+------------+---------+
| Parameter  | Description                                                                      | Range      | Default |
+============+==================================================================================+============+=========+
| preference | set desired disjoint constraint for Secondary LSP in compare to Primary LSP path | | strict   | strict  |
|            |                                                                                  | | avoid    |         |
+------------+----------------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# disjoint-preference avoid


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-secondary)# no disjoint-preference

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
