show evpn summary
-----------------

**Minimum user role:** operator

To show the mac-table for an EVPN instance.

**Command syntax: show evpn summary**

**Command mode:** operational


**Example**
::

    dnRouter# show evpn summary

        Global EVPN parameters
        MAC table limit      : 64000
        MAC table aging time : 320s
        Control Word         : enabled
        FAT Label            : disabled

        Number of EVPN instances       : 2
        Total local MAC addresses      : 1
        Total local MAC-IPs            : 0
        Total remote MAC addresses     : 0
        Total remote MAC-IPs           : 0
        Total MAC addresses            : 1
        Total MAC-IPs                  : 0
        Total suppressed MAC addresses : 0
        Total number of interfaces/up  : 2/2
        Total number of neighbors      : 2


        | Name   | Neighbors   | Interfaces/Up   | Local MACs / MAC-IPs   | Remote MACs / MAC-IPs   | Suppressed MACs   |
        |--------+-------------+-----------------+------------------------+-------------------------+-------------------|
        | evpn1  | 2           | 1/1             | 1/0                    | 0/0                     | 0                 |
        | evpn2  | 1           | 1/1             | 0/0                    | 0/0                     | 0                 |

           
.. **Help line:** show a summary of the information of the EVPN services

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+