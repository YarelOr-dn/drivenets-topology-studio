protocols rsvp tunnel secondary bfd
-----------------------------------

**Minimum user role:** operator

Define BFD behavior for protecting the RSVP-TE tunnel secondary LSP.
When BFD is enabled for the RSVP-TE tunnel, and the tunnel is set with end-to-end protection using secondary LSP, the BFD session will be established for secondary LSP as well.
The secondary LSP is dependent on BFD session and will be installed only if the BFD session is in Up state.
The operator can control the BFD timers desired for Secondary LSP protecting session.
To enter the RSVP-TE tunnel secondary lsp bfd configuration level:


**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary

**Note**

- The BFD settings apply to the LSP installed as the tunnel end-to-end protection alternate path.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# bfd
    dnRouter(cfg-tunnel-secondary-bfd)#


**Removing Configuration**

To revert all bfd configuration to default:
::

    dnRouter(cfg-rsvp-tunnel-secondary)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
