protocols isis instance timers lsp-refresh
------------------------------------------

**Minimum user role:** operator

The refresh interval determines the rate at which LSPs containing different sequence numbers are regenerated. This is done to keep the database information fresh.

To configure the refresh rate:

**Command syntax: lsp-refresh [interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance timers

**Note**

- The configuration applies to all isis levels

- lsp-lifetime interval must >= 300 + lsp-refresh.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| interval  | The minimum interval (in seconds) between regeneration of LSPs containing        | 1-65235 | 900     |
|           | different sequence numbers.                                                      |         |         |
|           | The set interval must be lower than the lsp-lifetime timer.                      |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# timers
    dnRouter(cfg-isis-inst-timers)# lsp-refresh 100


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-isis-inst-timers)# no lsp-refresh

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 6.0     | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| 9.0     | Moved to IS-IS global timers, removed level-1 and level-1-2 routing |
+---------+---------------------------------------------------------------------+
