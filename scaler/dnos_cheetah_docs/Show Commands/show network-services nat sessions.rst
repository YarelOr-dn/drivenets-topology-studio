show network-services nat ssessions
-----------------------------------

**Minimum user role:** operator

**Description:** To display the NAT sessions per NAT instance:


**Command syntax: show network-services nat sessions [instance-name]** [[intenal-ip [ipv4-address]] [internal-port [L4-port/ICMP-ID]] [external-ip [ipv4-address]] [external-port [L4-port/ICMP-ID]] [protocol [IP-protocol]] [type [snat/dnat]]]

**Command mode:** operational

**Parameter table**

+----------------+---------------------------------------------------------------------------+---------------+-----------+
| Parameter      | Description                                                               | Range         | Default   |
+================+===========================================================================+===============+===========+
| instance-name  | NAT instance name                                                         | String        | \-        |
+----------------+---------------------------------------------------------------------------+---------------+-----------+
| <filters>      | 5-tuple optional filters:                                                 |               | \-        |
|                |  - internal-ip: IPv4 address in the private domain (pre-translation)      | ipv4-address  | \-        |
|                |  - internal-port: L4-port/ICMP-ID in the public domain (pre-translation)  | 0..65535      | \-        |
|                |  - external-ip: IPv4 address in the public domain (post-translation)      | ipv4-address  | \-        |
|                |  - external-port: L4-port/ICMP-ID in the public domain (post-translation) | 0..65535      | \-        |
|                |  - protocol: IP protocol                                                  | TCP/UDP/ICMP  | \-        |
|                |  - type: translation type                                                 | SNAT/DNAT     | \-        |
+----------------+---------------------------------------------------------------------------+---------------+-----------+

**Note:**

- The “show network-services nat sessions” output features tables with the first 1000 sessions that match the specified session filter (max-acl for bypass).

- “show network-services nat sessions” matches the sessions according to the following order:

-- Sessions derived from the static 1:1 NAPT rules

-- Sessions derived from the static 1:1 NAT rules

-- Sessions learned according to the dynamic N:1 NAPT rules

-- Sessions learned according to the dynamic N:M NAT rules

- The filter may be a full 5-tuple pattern or a partial/empty tuple.

-- If a specific parameter is not specified as part of the filter, the missing parameter shall be referred as '*'

-- If the filter is not specified at all, the first 1000 sessions in the NAT session table will be presented according to the order defined above.

**Example**
::

        dnRouter# show network-services nat sessions nat-att-pepsi

        First 1000 matched sessions:

        | ID     | type        | Internal IP | Internal port / ICMP | External IP | External port / ICMP ID | Protocol | Timeout | Matched    | 
        |--------+-------------+-------------+----------------------+-------------+-------------------------+----------+---------+------------|
        | 123423 | snat        | 10.1.1.1    | 12312                | 200.1.1.1   | 80                      |  TCP     | 120 sec | 123123 pkts|
        | 123424 | snat        | 10.1.1.1    | 12314                | 200.1.1.1   | 80                      |  TCP     | 120 sec | 123123 pkts|
        | 123425 | dnat        | 20.1.1.1    | 12315                | 30.1.1.1    | 443                     |  TCP     | 58 sec  | 1232 pkts  |
        | 123426 | snat        | 10.2.1.2    | any                  | 200.2.1.2   | any                     |  any     | 58 sec  | 1232 pkts  |
        | 123427 | snat        | 10.1.1.3    | 1                    | 200.3.3.3   | 2                       |  ICMP    | 58 sec  | 1232 pkts  |

        Total filter matches: 5

        Matched bypass rules:

        | ID   | Src IP (Internal IP) | Dest IP       | Protocol | Matched            |
        +------+----------------------+---------------+----------+--------------------+
        | 0    | 10.2.5.116           | 20.2.5.116    | TCP      | 0                  |
        | 1    | 10.2.8.146           | 20.2.8.146    | TCP      | 0                  |
        | 2    | 10.2.8.227           | 20.2.8.227    | TCP      | 0                  |

        Total filter matches: 3

        First 100 matched IP-fragmented rules:

        | ID   | type        | Internal IP   | Internal port / ICMP ID | External IP   | External port / ICMP ID | Protocol | Original IP-ID | Translated IP-ID | Timeout  | Matched            | Direction |
        +------+-------------+---------------+-------------------------+---------------+-------------------------+----------+----------------+------------------+-------------------------------+-----------+
        | 0    | snat        | 10.1.1.1      | 1089                    | 201.1.1.1     | 2529                    | TCP      | 11             | 105              | 120      | 123123             | inbound   |
        | 1    | snat        | 201.1.1.1     | 9039                    | 10.1.1.1      | 3259                    | TCP      | 110            | 12               | 0        | 1                  | outbound  |
        | 2    | dnat        | 10.1.1.2      | 8080                    | 201.1.1.2     | 80                      | TCP      | 22             | 20               | 100      | 1                  | outbound  |
        | 3    | snat        | 10.1.1.1      | 3100                    | 201.1.1.1     | 1214                    | TCP      | 4              | 1                | 0        | 1                  | inbound   |


        dnRouter# show network-services nat sessions nat-att-pepsi internal-ip 10.1.1.1 internal-port 12312 external-ip 200.1.1.1 external-port 80 protocol TCP type snat

        First 1000 matched sessions:

        | ID     | type        | Internal IP | Internal port | External IP | External port | Protocol | Timeout | Matched             |
        |--------+-------------+-------------+---------------+-------------+---------------+----------+---------+---------------------|
        | 123423 | snat        | 10.1.1.1    | 12312         | 200.1.1.1   | 80            |  TCP     | 58      | 1232                |

        Total filter matches: 1

        No bypass rules matching the filter

        No IP-fragmented rules matching the filter

.. **Help line:** show network-services nat sessions [nat-instance]

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
