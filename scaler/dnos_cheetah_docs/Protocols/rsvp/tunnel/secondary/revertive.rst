protocols rsvp tunnel secondary revertive
-----------------------------------------

**Minimum user role:** operator

The tunnel revertive logic only applies for tunnels set with end-to-end protection, i.e usage of Primary & Secondary LSP.
Upon a Primary LSP failure (or an explicit request by the user), it is expected that traffic will shift from a Primary LSP to a Secondary LSP. 
The tunnel remains in an Up state and the Secondary LSP is the one declared as ”in-use” while passing traffic.
The revertive logic dictates if & when traffic should switch back to a Primary LSP assuming such was restored, established and is in an Up state.

To set a desire revertive behavior:

**Command syntax: revertive [revertive]**

**Command mode:** config

**Hierarchies**

- protocols rsvp tunnel secondary

**Parameter table**

+-----------+----------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                          | Range | Default |
+===========+======================================================================+=======+=========+
| revertive | Define when it is expected for traffic to switch back to primary lsp | \-    | 0       |
+-----------+----------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# secondary
    dnRouter(cfg-rsvp-tunnel-secondary)# revertive 600


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-rsvp-tunnel-secondary)# no revertive

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
