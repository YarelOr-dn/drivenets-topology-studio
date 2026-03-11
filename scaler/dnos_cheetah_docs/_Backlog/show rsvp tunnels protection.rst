show rsvp tunnels protection
----------------------------

**Command syntax: show rsvp tunnels protection** {name [tunnel-name] \| destination [destination] }

**Description:** displays tunnels bypass protection status

**CLI example:**
::

	dnRouter# show rsvp tunnels protection

	Legend: * - Make-Before-Break

	Destination     Source          Egress-IF            Role     State   FRR-State FRR-IF               Name
	-------------------------------------------------------------------------------------------------------------
	100.0.0.2       101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp2_P_CC_D_R1_7
	100.0.0.2       101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp2_P_CC_P_R1_8
	100.0.0.2       101.0.0.18      -                    head     AdminDn NoProt    -                    to-p2
	100.0.0.3       101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp3_P_CC_D_R1_5
	100.0.0.3       101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp3_P_CC_P_R1_6
	100.0.0.3       101.0.0.18      -                    head     AdminDn NoProt    -                    to-p3
	100.0.0.3       101.0.0.18      bundle-1718          head     up      NoProt    -                    to-p31
	101.0.0.16      101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp16_P_CC_D_R1_1
	101.0.0.16      101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp16_P_CC_P_R1_2
	101.0.0.17      101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp17_P_CC_D_R1_3
	101.0.0.17      101.0.0.18      bundle-1718          head     up      NoProt    -                    auto_tunnel_sysp18_sysp17_P_CC_P_R1_4
	101.0.3.210     101.0.0.18      -                    head     down    NoProt    -                    FLAPPING-P18-P210-DEFAULT
	101.0.3.210     101.0.0.18      -                    head     down    NoProt    -                    FLAPPING-P18-P210-PRIORITY

**Command mode:** operational

**TACACS role:** viewer

**Note:**

-  set name to display detailed information for tunnels matching the name

-  set destination to display detailed information for tunnels matching the destination

-  make-before-break indicates that tunnel is going through MBB and has multiple lsps

**Help line:**

**Parameter table:**

+-------------+---------------+---------------+
| Parameter   | Values        | Default value |
+=============+===============+===============+
| tunnel-name | string        |               |
|             |               |               |
|             | length 1..255 |               |
+-------------+---------------+---------------+
| destination | A.B.C.D       |               |
+-------------+---------------+---------------+
