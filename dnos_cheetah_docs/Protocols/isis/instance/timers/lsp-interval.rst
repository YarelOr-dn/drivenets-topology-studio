protocols isis instance timers lsp-interval
-------------------------------------------

**Minimum user role:** operator

You can set the minimum amount of time (in milliseconds) between consecutive lsp packets that are transmitted on a given interface.

To configure the interval:

**Command syntax: lsp-interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols isis instance timers

**Note**

- The first packet to be sent on an interface will be transmitted immediately.

- If lsp-interval has been reconfigured, it will only take effect after the next packet is transmitted.

**Parameter table**

+-----------+-------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                       | Range   | Default |
+===========+===================================================================+=========+=========+
| interval  | The minimum interval (in seconds) between consecutive LSP packets | 0-10000 | 0       |
+-----------+-------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# timers
    dnRouter(cfg-isis-inst-timers)# lsp-interval 33


**Removing Configuration**

To revert to the default interval:
::

    dnRouter(cfg-isis-inst-timers)# no lsp-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
