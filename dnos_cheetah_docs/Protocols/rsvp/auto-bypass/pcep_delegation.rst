protocols rsvp auto-bypass pcep delegation
------------------------------------------

**Minimum user role:** operator

PCEP delegation enables to configure the use of PCEP to delegate tunnel settings to a remote PCE. See additional information on PCE and PCEP in "mpls traffic-engineering pcep”.
When a new LSP is established for a tunnel, the path computation client (PCC) revokes the PCE's explicit route object (ERO) constraint. This may result in a new path with a different ERO for the tunnel. To prevent this behavior, use the sticky-ero attribute. With sticky-ero enabled, the following behavior is observed:

- The path computation client (PCC) keeps the last successfully established ERO received from the PCE for new established LSPs for the tunnel. All other LSP parameters (e.g. bandwidth, admin-groups, etc.) remain unchanged.

- When the user applies a new path configuration (ERO) to the tunnel, the tunnel will continue using the ERO provided by the PCE. The new path will be used when the tunnel is no longer delegated or RSVP has restarted.

To configure PCEP delegation globally:

**Command syntax: pcep delegation [admin-state]** sticky-ero [sticky-ero]

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-bypass

**Note**
.. -  'delegation disable' - disable delegation. sticky-ero-admin-state configuration remain unchanged

.. -  'no pcep delegation [delegation-admin-state] sticky-ero', 'no pcep delegation [delegation-admin-state] sticky-ero [sticky-ero-admin-state]' - return sticky-ero-admin-state to default settings

.. -  'no pcep delegation', 'no pcep delegation [delegation-admin-state]' - return both delegation-admin-state and sticky-ero-admin-state to default values

- When PCEP delegation is enabled, you still have control over tunnel configuration.

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
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# pcep delegation enabled sticky-ero enabled


**Removing Configuration**

To revert to the default sticky-ero state:
::

    dnRouter(cfg-protocols-rsvp)# no pcep delegation enabled sticky-ero

To revert to the default delegation state and sticky-ero-admin-state:
::

    dnRouter(cfg-protocols-rsvp)# no pcep delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
