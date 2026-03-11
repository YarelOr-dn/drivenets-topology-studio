protocols rsvp tunnel secondary admin-state
-------------------------------------------

**Minimum user role:** operator

With the secondary path, primary lsp of tunnel will be end to end protected. Upon a primary path failure, the traffic will switch to use the pre-installed secondary path.
The tunnel secondary lsp has a disjoin path with primary lsp
To enable usage of the tunnel secondary lsp:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary

**Note**
- Secondary LSP is not supported for bypass tunnels.

**Parameter table**

+-------------+----------------------------+--------------+----------+
| Parameter   | Description                | Range        | Default  |
+=============+============================+==============+==========+
| admin-state | Set tunnel secondary state | | enabled    | disabled |
|             |                            | | disabled   |          |
+-------------+----------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-rsvp-tunnel-secondary)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
