show segment-routing pcc lsp-db
-------------------------------

**Minimum user role:** viewer

To display segment-routing pcc lsp-db report information associated with a policy

**Command syntax: show segment-routing pcc lsp-db policy [policy-name]** {detail}

**Command mode:** operational

**Parameter table**

+---------------------+-----------------------------------------------------------------------------------------+
| Parameter           | Description                                                                             |
+=====================+=========================================================================================+
| policy-name         | Displays brief information for lsp reports associated with policy matching policy name. |
+---------------------+-----------------------------------------------------------------------------------------+
| detail              | Displays detailed information for lsp reports for SR-TE policy.                         |
+---------------------+-----------------------------------------------------------------------------------------+

**Example**
::

  dnRouter# show segment-routing pcc lsp-db policy pol1
  Path Name                 Path-id     SRP         D/S/R/A/C   Protection      State
  ----------------------------------------------------------------------------------------
  pol1_pcep_path            2           3           1/0/0/1/0   P:1 S:0 (PT:8)  up
  pol1_via34                1           0           0/0/0/1/0   P:0 S:0 (PT:8)  active

  dnRouter# show segment-routing pcc lsp-db policy pol1 detail
  Policy: pol1 (265)
  Destination: 4.4.4.4 Color: 0
  pol1_pcep_path
      Srp object:
          Srp-id: 1, Flags: 0x0, Path setup type: SR
      Lsp object:
          Source: 1.1.1.1, Destination: 4.4.4.4, Tunnel-id: 265, Lsp-id: 0
          Plsp-id: 2, flags: D:1 S:0 R:0 A:1 C:0 Operational: up
      Association object:
          R:0, ID:1 Source: 1.1.1.1
          Type: Path Protection Association
              Type: 1:1 Unidirectional Protection
              P:1, S:0
      Association object:
          R:0, ID:1 Source: 1.1.1.1
          Type: SR Policy Association
              Extended ID:
                  Color: 0, Endpoint:4.4.4.4
              Path Candidate ID:
                  Origin: Static, Disc: 2
                  Originator: 1.1.1.1, ASN: 1233
              Policy Name: pol1
              Path Name: pcep_path
              Path Preference: 10
      ERO:
          SID[0]: 0, NAI: 12.0.0.1, RemoteAddress: 12.0.0.2, Flags: 0x4 (loose)
          SID[1]: 0, NAI: 23.0.0.2, RemoteAddress: 23.0.0.3, Flags: 0x4 (loose)
      Attributes: priority: setup 7, hold 0

  pol1_via34
      Lsp object:
          Source: 1.1.1.1, Destination: 4.4.4.4, Tunnel-id: 265, Lsp-id: 0
          Plsp-id: 1, flags: D:0 S:0 R:0 A:1 C:0 Operational: active
      Association object:
          R:0, ID:1 Source: 1.1.1.1
          Type: Path Protection Association
              Type: 1:1 Unidirectional Protection
              P:0, S:0
      Association object:
          R:0, ID:1 Source: 1.1.1.1
          Type: SR Policy Association
              Extended ID:
                  Color: 0, Endpoint:4.4.4.4
              Path Candidate ID:
                  Origin: Static, Disc: 1
                  Originator: 1.1.1.1, ASN: 1234
              Policy Name: pol1
              Path Name: via34
              Path Preference: 20
      ERO:
          SID[0]: 0, NAI: 12.0.0.1, RemoteAddress: 0.0.0.0, Flags: 0x4 (strict)
          SID[1]: 0, NAI: 23.0.0.2, RemoteAddress: 0.0.0.0, Flags: 0x4 (strict)
          SID[2]: 0, NAI: 34.0.0.3, RemoteAddress: 0.0.0.0, Flags: 0x4 (strict)
      Attributes: priority: setup 7, hold 0

.. **Help line:** Displays segment-routing pcc lsp-db information

**Command History**

+---------+-----------------------------------------------------------------------------------------------+
| Release | Modification                                                                                  |
+=========+===============================================================================================+
| 19.0    | Command introduced                                                                            |
+---------+-----------------------------------------------------------------------------------------------+
