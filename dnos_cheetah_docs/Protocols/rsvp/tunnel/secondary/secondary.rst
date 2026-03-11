protocols rsvp tunnel secondary
-------------------------------

**Minimum user role:** operator

To configure a tunnel secondary lsp:

**Command syntax: secondary**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel

**Note**
- Secondary LSP is not supported for bypass tunnels.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)#


**Removing Configuration**

To revert all secondary LSP's configuration to default:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no secondary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
