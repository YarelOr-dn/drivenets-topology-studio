protocols rsvp tunnel bypass primary path-options path dynamic
--------------------------------------------------------------

**Minimum user role:** operator

You can instruct the tunnel to resolve the LSP dynamically or using a specific explicit path. These can be complementary such that the explicit path may have holes that are resolved dynamically, using CSPF.

You can configure up to 10 paths altogether (explicit and dynamic) under a tunnel.

To configure the path-options for the tunnel so that the LSP will follow the explicit path rules:

**Command syntax: path dynamic**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel bypass primary path-options
- protocols rsvp tunnel primary path-options
- protocols rsvp tunnel secondary path-options
- protocols rsvp auto-mesh tunnel-template primary path-options

**Note**
- When configuring path-options (see "rsvp tunnel primary path-options"), you must configure a path-options path.

- You can configure path dynamic only once per path-option.

.. - If you instruct the tunnel to use explicit tunnels only and all path options fail, the tunnel will not be established. If you configure explicit path for higher priority path-options than for path-dynamic, the explicit path will never be tested.

.. - If you set "path dynamic" with a higher "path-options priority" than "path explicit", then the explicit path will never be considered. "path dynamic" should therefore always be the last option.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# primary

    dnRouter(cfg-rsvp-tunnel-primary)# path-options 3
    dnRouter(cfg-tunnel-primary-path-options)# path dynamic


**Removing Configuration**

To revert to the default path behavior:
::

    dnRouter(cfg-tunnel-primary-path-options)# no path

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
