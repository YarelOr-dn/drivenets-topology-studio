show ldp binding
----------------

**Minimum user role:** viewer

To display the content of the label information base (LIB):



**Command syntax: show ldp** [address-family] **binding** [prefix] [binding-type]

**Command mode:** operational



.. **Note**

    - ipv4-address is optional, if not specified, displays all neighbors binding

**Parameter table**

+----------------+---------------------------------------------------------------------------------+-----------+
| Parameter      | Description                                                                     | Range     |
+================+=================================================================================+===========+
| address-family | Display LIB for a specific address-family                                       | IPv4      |
+----------------+---------------------------------------------------------------------------------+-----------+
| prefix         | Display LIB for a specific prefix                                               | A.B.C.D/x |
+----------------+---------------------------------------------------------------------------------+-----------+
| binding-type   | ldp sr srte-sc tunnel                                                           | \-        |
+----------------+---------------------------------------------------------------------------------+-----------+
| ldp            | Display information for binding with LDP based egress labels                    | \-        |
+----------------+---------------------------------------------------------------------------------+-----------+
| sr             | Display information for binding with IGP segment-routing egress labels          | \-        |
+----------------+---------------------------------------------------------------------------------+-----------+
| srte-sc        | Display information for binding with IGP-SC using SR-TE policy egress labels    | \-        |
+----------------+---------------------------------------------------------------------------------+-----------+
| tunnel         | Display information for binding with RSVP tunnels using LDP based egress labels | \-        |
+----------------+---------------------------------------------------------------------------------+-----------+

**Example**
::

        dnRouter# show ldp binding
        4.4.4.4/32
        Local binding: label: 57232
        Exists in local IGP table: yes
        Exists in local IGP-Shortcut table: no
        Binding uptime: 00:00:35
        Remote bindings:

                LDP Peer         Label        Uptime
                --------         --------     --------
                2.2.2.2          57231        00:01:13
                3.3.3.3          57229        00:01:14

                SR-IGP-nexthop   Label        Uptime
                --------         --------     --------
                142.0.0.4        imp-null     00:01:13 (installed)
                141.0.0.4        imp-null     00:01:13 (installed)

        5.5.5.5/32
        Local binding: label: 57229
        Exists in local IGP table: yes
        Exists in local IGP-Shortcut table: no
        Binding uptime: 00:03:57
        Remote bindings:

                LDP Peer         Label        Uptime
                --------         --------     --------
                3.3.3.3          57230        00:11:41
                2.2.2.2          57229        00:11:42

                SR-IGP-nexthop   Label        Uptime
                --------         --------     --------
                15.0.0.5         imp-null     00:12:19

                SRTE-SC-nexthop  Label-Dest   Uptime
                --------         --------     --------
                policy_a         -            00:04:51 (installed)

    dnRouter# show ldp binding 4.4.4.4/32
    4.4.4.4/32
        Local binding: label: 57224
        Exists in local IGP table: yes
        Binding uptime: 00:00:28
        Remote bindings:

            LDP Peer         Label        Uptime
            --------         --------     --------
             3.3.3.3         57229        00:00:28
             2.2.2.2         57229        00:00:28

            SR-IGP-nexthop   Label        Uptime
            --------         --------     --------
            142.0.0.4        imp-null     00:00:28 (installed)
            141.0.0.4        imp-null     00:00:28 (installed)


    dnRouter# show ldp binding ldp
    4.4.4.4/32
        Local binding: label: 57221
        Exists in local IGP table: yes
        Binding uptime: 00:00:14
        Remote bindings:

            LDP Peer         Label        Uptime
            --------         --------     --------
            3.3.3.3          57235        00:00:14
            2.2.2.2          57235        00:00:14
            5.5.5.5          57222        00:00:14 (installed)

    5.5.5.5/32
        Local binding: label: 57222
        Exists in local IGP table: yes
        Binding uptime: 00:00:14
        Remote bindings:

        LDP Peer         Label        Uptime
            --------         --------     --------
            3.3.3.3          57236        00:00:14
            2.2.2.2          57236        00:00:14
            5.5.5.5          imp-null     00:00:14 (installed)


    dnRouter# show ldp binding sr
    4.4.4.4/32
        Local binding: label: 57221
        Exists in local IGP table: yes
        Binding uptime: 00:00:14
        Remote bindings:

            SR-IGP-nexthop   Label        Uptime
            --------         --------     --------
            16.0.0.6         16004        00:00:14
            15.0.0.5         16004        00:00:14

    5.5.5.5/32
        Local binding: label: 57222
        Exists in local IGP table: yes
        Binding uptime: 00:00:14
        Remote bindings:

            SR-IGP-nexthop   Label        Uptime
            --------         --------     --------
            15.0.0.5         imp-null     00:00:14


        dnRouter# show ldp binding srte-sc
        4.4.4.4/32
        Local binding: label: 57232
        Exists in local IGP table: yes
        Exists in local IGP-Shortcut table: no
        Binding uptime: 00:05:55
        Remote bindings:

            SRTE-SC-nexthop  Label-Dest   Uptime
            --------         --------     --------
            policy_a         16004        00:00:15 (installed)
            policy_b         16004        00:00:15 (installed)

        dnRouter# show mpls ldp binding 4.4.4.4/32 tunnel
        4.4.4.4/32
        Local binding: label: 57225
        Exists in local IGP table: yes
        Exists in local IGP-Shortcut table: yes
        Binding uptime: 00:01:41
        Remote bindings:

            LDP Peer         Label        Uptime
            --------         --------     --------
            3.3.3.3          57226        00:01:13 (installed)

.. **Help line:** Displays the contents of the LIB

**Command History**

+---------+-------------------------------------------------------------------------+
| Release | Modification                                                            |
+=========+=========================================================================+
| 6.0     | Command introduced                                                      |
+---------+-------------------------------------------------------------------------+
| 15.0    | Added support for displaying ldp-based and sr-based binding information |
+---------+-------------------------------------------------------------------------+
| 15.1    | Added support for displaying binding information under binding-type     |
+---------+-------------------------------------------------------------------------+


