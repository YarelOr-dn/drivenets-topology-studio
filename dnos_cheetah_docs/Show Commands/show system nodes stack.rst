show system nodes stack
-----------------------

**Command syntax: show system nodes stack**

**Description:** Displays detailed information about packages in current, revert and target stacks relevant per each node in the cluster.

**CLI example:**
::

	dnRouter# show system nodes stack

	Current stack:

    | Node | ID | Component       | HW Model      | HW Revision   | Version     | Package name                | Size    | Authenticity        | MD5           |
    |------+----|-----------------+---------------+---------------+-------------+-----------------------------+---------+---------------------+---------------|
    | NCC  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_14.0.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCC  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.304.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCM  | A0 | NCM-NOS         |     -         |     _         | 3.0.0       | drivenets_stratax_3.0.0.tar | 3.0 GB  | signature-verified  | hsjgj63478x   |
    | NCP  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_14.0.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCP  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.304.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCP  | 0  | Firmware        | S9700-53DX    | 1             | 7.80        | ufi-wbx-fw-7.80             | 40 MB   | hash-verified       | jhsdgsdj674   |
    | NCF  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_14.0.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCF  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.304.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCF  | 0  | Firmware        | S9700-23D-J   | 3             | 7.80        | ufi-wbx-fw-7.80             | 40 MB   | hash-verified       | jhsdgsdj674   |

	Target stack:

    | Node | ID | Component       | HW Model      | HW Revision   | Version     | Package name                | Size    | Authenticity        | MD5           |
    |------+----|-----------------+---------------+---------------+-------------+-----------------------------+---------+---------------------+---------------|
    | NCC  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_16.1.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCC  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.506.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCM  | A0 | NCM-NOS         |     -         |     _         | 3.0.0       | drivenets_stratax_3.0.0.tar | 3.0 GB  | signature-verified  | hsjgj63478x   |
    | NCP  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_16.1.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCP  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.506.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCP  | 0  | Firmware        | S9700-53DX    | 1             | 7.80        | ufi-wbx-fw-8.10             | 40 MB   | hash-verified       | jhsdgsdj674   |
    | NCF  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_16.1.1.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCF  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.506.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |


	Revert stack:

    | Node | ID | Component       | HW Model      | HW Revision   | Version     | Package name                | Size    | Authenticity        | MD5           |
    |------+----|-----------------+---------------+---------------+-------------+-----------------------------+---------+---------------------+---------------|
    | NCC  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_13.0.2.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCM  | A0 | NCM-NOS         |     -         |     _         | 2.0.0       | drivenets_stratax_2.0.0.tar | 3.0 GB  | signature-verified  | hsjgj63478x   |
    | NCP  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_13.0.2.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCP  | 0  | BaseOS          |     -         |     -         | 2.304       | drivenets_baseos_2.304.tar  | 1.0 GB  | signature-verified  | 2467asdghfs   |
    | NCP  | 0  | Firmware        | S9700-53DX    | 1             | 7.80        | ufi-wbx-fw-7.80             | 40 MB   | hash-verified       | jhsdgsdj674   |
    | NCF  | 0  | DNOS            |     -         |     -         | 14.0.1      | drivenets_dnos_13.0.2.tar   | 2.8 GB  | signature-verified  | azn32564asv   |
    | NCF  | 0  | Firmware        | S9700-23D-J   | 3             | 7.80        | ufi-wbx-fw-7.80             | 40 MB   | hash-verified       | jhsdgsdj674   |

**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** Displays detailed information about packages in current, revert and target stacks per each node in the cluster

**Outputs table:**

+----------------------+-------------------------+----------+
| Parameter            | Values                  | Comments |
+======================+=========================+==========+
| Authenticity         | signature-verified      |          |
|                      | hash-verified           |          |
|                      | unverified              |          |
+----------------------+-------------------------+----------+