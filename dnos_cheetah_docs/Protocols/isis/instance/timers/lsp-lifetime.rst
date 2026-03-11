protocols isis instance timers lsp-lifetime
-------------------------------------------

**Minimum user role:** operator

The LSP lifetime interval determines the maximum amount of time that LSPs can remain in the router's database without being refreshed. You may need to adjust the maximum LSP lifetime if you change the LSP refresh interval.

To configure the lifetime interval:

**Command syntax: lsp-lifetime [interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance timers

**Note**

- The configuration applies to all IS-IS levels

- lsp-lifetime interval must >= 300 + lsp-refresh.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| interval  | The maximum time (in seconds) that an LSP can remain in the router's database    | 360-65535 | 1200    |
|           | without being refreshed.                                                         |           |         |
|           | The set interval must be higher than the set lsp-refresh timer.                  |           |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# timers
    dnRouter(cfg-isis-inst-timers)# lsp-lifetime 1000


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-isis-inst-timers)# no lsp-lifetime

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 6.0     | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 9.0     | Moved to IS-IS global timers, removed level-1 and level-1-2 routing |
+---------+---------------------------------------------------------------------+
