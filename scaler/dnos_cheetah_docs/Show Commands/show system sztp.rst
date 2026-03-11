show system sztp
----------------

**Minimum user role:** viewer

To display SZTP flow status, last attempt state and the configured servers and certificates for SZTP, use the show system sztp command.


**Command syntax: show system sztp**

**Command mode:** operational

**notes**

- In case bootstrap server trust anchor list is empty, The actual trust anchor list is the global anchor list

**Parameter table**

The command displays the following sections and parameters:

General SZTP Flow status

+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+
| Field                        | Description                                                                    | Range                                              |
+==============================+================================================================================+====================================================+
| SZTP admin-state             | The administrative state of Secure Zero Touch Provisioning (SZTP)              | Enabled, Disabled                                  |
+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+
| SZTP flow status             | Current status of the SZTP flow                                                | In-Progress, Inactive, Awaiting, Restoring-Failed  |
+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+
| Total Flow Duration          | Total time taken for the SZTP process from the beginning                       | D days, HH:MM:SS                                   |
+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+
| Number of Bootstrap attempts | The number of times the SZTP bootstrap process has been initiated              | integer                                            |
+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+
| Retry Interval               | The configured time between retries                                            | 5..3600 (seconds)                                  |
+------------------------------+--------------------------------------------------------------------------------+----------------------------------------------------+


Current Attempt status parameters

+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Field                        | Description                                                                                  | Range                                                                                                    |
+==============================+==============================================================================================+==========================================================================================================+
| Bootstrap Server             | The IP address or hostname of the current bootstrap server being contacted                   | A.B.C.D / x:x::x:x / hostname                                                                            |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Port                         | The TCP port number used when connecting to the bootstrap server                             | 0..65535                                                                                                 |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Priority                     | The preference level of the bootstrap server, with lower numerical values as higher priority | 1..255                                                                                                   |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Current step                 | The current SZTP process step indicator                                                      | Establish-Connection / Bootstrap-Initiated / Parsing-Initiated / Boot-Image-Initiated / Config-initiated |
|                              |                                                                                              | Parsing-Error / Boot-Image-Error / Config-Error                                                          |
|                              |                                                                                              | Boot-Image-Mismatch / Boot-Image-Installed-Rebooting / Bootstrap-Complete                                |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Sub step                     | Additional details about the current step in the process                                     | Download-Stack / Precheck / Install / Apply-Config / Commit-Config                                       |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Restore step                 | In case SZTP not in restore this filed will be empty, otherwise will include the stage of    | none, restore-configuration, restore-boot-image,                                                         |
|                              | restore, of the stage of failed-restore                                                      | restore-configuration-failed, restore-boot-image-failed                                                  |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Step duration                | Duration taken for the current step                                                          | D days, HH:MM:SS                                                                                         |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+
| Attempt Duration             | The time elapsed for the current attempt at the SZTP process                                 | D days, HH:MM:SS                                                                                         |
+------------------------------+----------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------+



Configured bootstrap servers and certificates


+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Field                        | Description                                                                           | Range                                                    |
+==============================+=======================================================================================+==========================================================+
| Device Certificate name      | The identifier for the device certificate used in SZTP                                | String                                                   |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Server Address               | IP address of the bootstrap servers listed                                            | A.B.C.D / x:x::x:x / string                              |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Port                         | The TCP port number used when connecting to the bootstrap server                      | 0..65535                                                 |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Priority                     | The preference level of the server, with lower numerical values as higher priority    | 1..255                                                   |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Trust Anchor List            | Trust anchor certificates associated with each bootstrap server                       | List of names (0..128 elements)                          |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Retry Interval               | The configured time between retries                                                   | 5..3600 (seconds)                                        |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+
| Vrf Name                     | The name of the VRF                                                                   | mgmt0, default                                           |
+------------------------------+---------------------------------------------------------------------------------------+----------------------------------------------------------+


**Example**
::

    dnRouter# show system sztp

    General Status
    --------------

    SZTP admin-state: Enabled
    SZTP flow status: in-progress
    Total Flow Duration: 0 days, 0:10:00
    Number of Bootstrap attempts : 1
    Retry Interval: 60 seconds

    Current Bootstrap Server Attempt
    -----------------------------------

    Bootstrap Server ::1
    Port: 443
    Priority: 1
    Current step: boot-image-mismatch
    Sub step: precheck
    Restore step: None
    Step duration: 0 days, 0:00:09
    Attempt Duration: 0 days, 0:10:00

    Configured bootstrap servers and certificates
    ---------------------------------------------

    Device Certificate name: device-cert
    Global Trust Anchor List: global1, global2

    SZTP Servers

    | Priority | Server Address    | Vrf Name | Port  | Trust Anchor List  |
    +----------+-------------------+----------+-------+--------------------+
    | 1        | ::1               | default  | 443   |                    |
    | 2        | ::2               | default  | 8443  | cert3              |
    | 3        | ::3               | default  | 443   |                    |
    +----------+-------------------+----------+-------+--------------------+

    DHCP acquired bootstrap servers servers
    ----------------------------------------

    Device Certificate name: device-cert
    Global Trust Anchor List: global1, global2

    SZTP Servers

    | Priority | Server Address    | Vrf Name | Port  |
    +----------+-------------------+----------+-------+
    | 256      | ::5               | mgmt0    | 443   |
    | 257      | ::6               | mgmt0    | 8443  |
    | 258      | ::7               | mgmt0    | 443   |
    +----------+-------------------+----------+-------+


.. **Help line:** show system sztp

**Command History**

+---------+---------------------------------------------------------------------+
| Release | Modification                                                        |
+=========+=====================================================================+
| 19.1    | Command introduced                                                  |
+---------+---------------------------------------------------------------------+
| TBD     | Added DHCP acquired servers list support                            |
+---------+---------------------------------------------------------------------+
