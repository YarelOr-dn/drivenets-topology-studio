show services ipsec terminators
--------------------------------------

**Minimum user role:** viewer

To show the state of the configure IPSec terminators.

**Command syntax: show services ipsec terminators** [terminator-id]

**Command mode:** operational

**Example**
::

	dnRouter# show services ipsec terminators

    | ID | Type        | Admin State | oper-state    |  Neighbor Interface | Internet vlan | IKE vlan   | #tunnels |
    +----+-------------+-------------+---------------+---------------------+---------------+------------+----------+
    | 1  | dpdk vm     | enabled     | up            |  ge100-0/0/0        | 300           | 200        | 12       |
    | 2  | dpdk vm     | enabled     | up            |  bundle-1           | 300           | 200        | 0        |



    dnRouter# show services ipsec terminators 1

    terminator 1
        admin-state: enabled
        oper-state: up
        Neighbor Interface: ge100-0/0/0
        Internet vlan: 300, IKE vlan: 200
        #tunnels: 12
            tenant:1, account:1
                | vrf-name | #tunnels   |
                +----------+------------+
                | 1        | 7          |
                | 2        | 3          |

            tenant:1, account:2
                | vrf-name | #tunnels   |
                +----------+------------+
                | 3        | 2          |



.. **Help line:** show IPSec terminators state and statistics

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
