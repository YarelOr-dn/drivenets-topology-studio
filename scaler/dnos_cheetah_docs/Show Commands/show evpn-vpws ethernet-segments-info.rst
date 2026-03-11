show evpn-vpws ethernet-segments-info
-------------------------------------

**Minimum user role:** operator

To show information relating to the ethernet-segments of EVPN-VPWS instance(s).

**Command syntax: show evpn-vpws ethernet-segments-info** instance [evpn-vpws-name] esi [esi-value]

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-----------------------------------------+---------------+
| Parameter          | Description                             | Values                                  | Default value |
+====================+=========================================+=========================================+===============+
| evpn-name          | The name of the EVPN instance           | String                       | all      | \-            |
+--------------------+-----------------------------------------+-----------------------------------------+---------------+
| esi-value          | The esi 10 byte value                   | String - 10 hex octets separated by ':' | \-            |
+--------------------+-----------------------------------------+-----------------------------------------+---------------+

**Note:**

- Specifying an evpn-vpws-name will display the information of the specified EVPN-VPWS instance.

- If no instance is specified, this will result in the listing of the ethernet-segment information for all the EVPN-VPWS instances.

- If the esi is specified then the ethernet-segment information for the specific esi will be shown.

**Example**
::

  dev-dnRouter# show evpn-vpws ethernet-segments-info instance evpn1 

  Codes: ! - Remote DF/BDF role misalignment

  EVPN-VPWS: evpn1
    EVI ID : 1
      Number of ESs: 2

      Flags | ESI                           | Nexthops             | Aliasing Label | Mode          | Role
      ----------------------------------------------------------------------------------------------------------
            | 00:00:00:00:00:00:00:00:00:00 | 52.52.52.52          | 119679         | -             | non-DF
            | 00:12:01:11:94:00:00:00:00:01 | bundle-1010.1200     | 118674         | single-active | non-DF
            |                               | 53.53.53.53          | 305174         | single-active | DF

  dev-dnRouter# show evpn-vpws ethernet-segments-info instance evpn1 esi 00:12:01:11:94:00:00:00:00:01

  Codes: ! - Remote DF/BDF role misalignment

  EVPN-VPWS: evpn1
    EVI ID : 1
      Number of ESs: 2

      Flags | ESI                           | Nexthops             | Aliasing Label | Mode          | Role
      ----------------------------------------------------------------------------------------------------------
            | 00:12:01:11:94:00:00:00:00:01 | bundle-1010.1200     | 118674         | single-active | non-DF
            |                               | 53.53.53.53          | 305174         | single-active | DF


.. **Help line:** show detailed information for EVPN-VPWS instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+