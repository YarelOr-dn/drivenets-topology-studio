show evpn-vpws detail
---------------------

**Minimum user role:** operator

To show the detailed information of an EVPN-VPWS instance.

**Command syntax: show evpn-vpws {instance [evpn-vpws-name]} detail**  

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| evpn-vpws-name     | The name of the EVPN-VPWS instance      | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying an evpn-vpws-name will display the information of the specified EVPN-VPWS instance.

- If no instance is specified, this will result in the listing of the detailed information for all the EVPN-VPWS instances.


**Example**
::


    dnRouter# show evpn-vpws detail

    EVPN-VPWS: EVPN-VPWS1
      EVI ID                 : 1
      Transport protocol     : mpls
      Route Distinguisher    : 101.3.3.3:1
      Admin state            : enabled
      Local AC Interface     : ge100-0/0/74.2222 (up / forwarding-all), Uptime: 0 days, 0:16:05
      Configured Homing Type : multi-homed
      Role                   : designated-forwarder
      Local-ESI              : 00:11:22:33:44:55:11:22:33:44
      Local VPWS-Service Id  : 2222
      Remote-ESI             : 00:00:00:00:00:00:00:00:00:00 
      Remote VPWS-Service Id : 1234
      State                  : up 
      Uptime                 : 0 days, 19:20:35  
      L2 MTU                 : 0
      MPLS Label             : 118671
      Control Word           : disabled
      FAT Label              : disabled

      Flags codes: P - primary, B - backup, ND - no-DF,
               F - FAT-label, C - Control-word, I - installed,
               A - All-Active, S-Single-active, s - Stale

      ESI: 00:00:00:00:00:00:00:00:00:00 (Selected remote ESI)
      Number of neighbors:  1

      | IP Address        | VPWS Service-Id   | Label    | L2 MTU   | Flags        | Failed reason              |
      +-------------------+-------------------+----------+----------+--------------+----------------------------+
      | 101.8.8.8         | 1234              | 118671   | 0        | ND/I         |                            |


      ESI: 00:00:00:00:00:00:00:00:00:11 (Unselected remote ESI)
      Number of neighbors:  1

      | IP Address        | VPWS Service-Id   | Label    | L2 MTU   | Flags        | Failed reason                |
      +-------------------+-------------------+----------+----------+--------------+------------------------------+
      | 101.8.8.9         | 1234              | 118671   | 0        | ND           | Multiple remote ESI received |

      ESI: 00:11:22:33:44:55:11:22:33:44 (Local ESI)
      Number of neighbors:  1

      | IP Address        | VPWS Service-Id   | Label    | L2 MTU   | Flags        | Failed reason              |
      +-------------------+-------------------+----------+----------+--------------+----------------------------+
      | 102.102.102.102   | 2222              | 100      | 0        | B/S          | Member of same local ESI   |


      VPWS Counters
      =============
      RX Octets   : 0
      RX Packets  : 0
      RX Rate     : 0 Mbps
      TX Octets   : 0
      TX Packets  : 0
      TX Rate     : 0 Mbps

      ESI: 00:11:22:33:44:55:11:22:33:44
        AC: ge100-0/0/74.2222 State: up / forwarding-all
        Requested Homing Type: multi-homed-single-active
        Actual Homing Type: multi-homed-single-active Role: designated-forwarder
        Service label               : 118671
        Designated Forwarder        : 101.3.3.3
        Backup Designated Forwarder : 102.102.102.102
        Time of Last DF Election    : 0 days, 0:19:01
        Requested Algorithm         : highest-preference (1000)
        Actual Algorithm            : mod


.. **Help line:** show detailed information for EVPN instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+