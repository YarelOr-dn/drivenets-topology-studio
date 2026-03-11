protocols rsvp auto-mesh tunnel-template pcep delegation
--------------------------------------------------------

**Minimum user role:** operator

PCEP delegation enables to configure the use of PCEP to delegate tunnel settings to a remote PCE. See additional information on PCE and PCEP in "mpls traffic-engineering pcep".
When PCEP delegation is enabled, you still have control over tunnel configuration.
When a new LSP is established for a tunnel, the path computation client (PCC) revokes the PCE's explicit route object (ERO) constraint. This may result in a new path with a different ERO for the tunnel. To prevent this behavior, use the sticky-ero attribute. With sticky-ero enabled, the following behavior is observed:

- The path computation client (PCC) keeps the last successfully established ERO received from the PCE for new established LSPs for the tunnel. All other LSP parameters (e.g. bandwidth, admin-groups, etc.) remain unchanged.

- When the user applies a new path configuration (ERO) to the tunnel, the tunnel will continue using the ERO provided by the PCE. The new path will be used when the tunnel is no longer delegated or RSVP has restarted.

To configure PCEP delegation for the tunnel, manual bypass tunnel, or auto-bypass tunnel:

**Command syntax: pcep delegation [admin-state]** sticky-ero [sticky-ero]

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template
- protocols rsvp tunnel
- protocols rsvp tunnel bypass

**Note**
- When PCEP delegation is enabled, you still have control over tunnel configuration.

- Tunnel delegation configuration takes precedence over global RSVP delegation configuration.

.. - 'delegation disable' - disable delegation. sticky-ero-admin-state configuration remain unchanged

.. - 'no pcep delegation', 'no pcep delegation [delegation-admin-state]' - return both delegation-admin-state and sticky-ero-admin-state to default values

**Parameter table**

+-------------+------------------------+--------------+---------+
| Parameter   | Description            | Range        | Default |
+=============+========================+==============+=========+
| admin-state | tunnel delegation mode | | enabled    | \-      |
|             |                        | | disabled   |         |
+-------------+------------------------+--------------+---------+
| sticky-ero  | tunnel delegation mode | | enabled    | \-      |
|             |                        | | disabled   |         |
+-------------+------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# pcep delegation enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# pcep delegation disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled sticky-ero enabled
    dnRouter(cfg-protocols-rsvp)# tunnel TUNNEL1
    dnRouter(cfg-protocols-rsvp-tunnel)# pcep delegation enabled sticky-ero disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# tunnel MAN_BACKUP_1 bypass
    dnRouter(cfg-protocols-rsvp-bypass-tunnel)# pcep delegation enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# auto-bypass
    dnRouter(cfg-protocols-rsvp-auto-bypass)# pcep delegation enabled


**Removing Configuration**

To revert to the default sticky-ero state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no pcep delegation enabled sticky-ero

To revert to the default delegation state and sticky-ero-admin-state:
::

    dnRouter(cfg-protocols-rsvp-tunnel)# no pcep delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
