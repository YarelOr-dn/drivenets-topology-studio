protocols rsvp timers lsp-establishment resv
--------------------------------------------

**Minimum user role:** operator

You can define how long a tunnel head will wait when a new LSP is signaled, before declaring signaling failure and continuing to establish a new LSP.
To configure the LSP establishment timer:

**Command syntax: lsp-establishment resv [resv-timeout]**

**Command mode:** config

**Hierarchies**

- protocols rsvp timers

**Parameter table**

+--------------+-----------------------------------------------+---------+---------+
| Parameter    | Description                                   | Range   | Default |
+==============+===============================================+=========+=========+
| resv-timeout | define the resv timeout for lsp establishment | 1-65535 | 135     |
+--------------+-----------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# lsp-establishment resv 15


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp-timers)# lsp-establishment resv

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+
