protocols rsvp auto-bypass bfd
------------------------------

**Minimum user role:** operator

An RSVP tunnel is a label-switched path (LSP) that can carry inside other RSVP LSPs in order to provide network end-to-end traffic engineering. Each tunnel LSP can have a unique BFD session. 

BFD is supported for all tunnel types (primary, manual bypass, auto bypass and auto mesh).

To establish the BFD session, LSP-Ping is used to sync the peers on session BFD discriminators.
Before activating an LSP, verify the data path by establishing BFD session over LSP and ensure that tunnel can carry data traffic. Only after the BFD session is up the LSP will be used for forwarding.

Install delay: before installing the new LSP as the active tunnel path in the data path, wait for "rsvp make-before-break install-delay" time to verify that LSP is stable as BFD session remain UP for install-delay time. 

After the time period, if the BFD is still up, install the tunnel in the data path.

Upon BFD failure:

- At head LER - Remove LSP, invoke Break Before Make and remove LSP from data path.
- At tail LER - Only Respond with BFD down
- BFD for RSVP isn't a trigger for bypass protection

In the case that RSVP FRR is enabled, BFD timers should be configured to at least 3 x 300 ms so that FRR mechanism can operate as expected and provide fast switchover to a bypass tunnel. it applies to any router acting as PLR, including the case where the head is the PLR of the tunnel.

BFD failure detection time is computed out of the negotiated received interval and the remote multiplier configurations. Detection-time = negotiated-received-interval X received multiplier.

This is the maximum amount of time that can elapse without receipt of a BFD control packet before the session is declared down.

BFD neighbor can signal session state down, and upon receipt, local BFD session will immediately switch to DOWN state.

To enter BFD configuration level:

**Command syntax: bfd**

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass
- protocols rsvp tunnel
- protocols rsvp auto-mesh tunnel-template

**Note**
.. -  BFD is supported for all tunnel types (primary, manual bypass, auto bypass, auto-mesh)

.. -  no command returns all bfd configuration to their default settings

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# bfd
    dnRouter(cfg-rsvp-tunnel-bfd)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# bfd
    dnRouter(cfg-rsvp-bypass-tunnel-bfd)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# bfd
    dnRouter(cfg-rsvp-auto-bypass-bfd)#


**Removing Configuration**

To revert all bfd configurations to their default values:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
