show network-services ipsec counters
------------------------------------

**Minimum user role:** viewer

To show state of IPSec tunnel counters

**Command syntax: show network-services ipsec counters [tunnel-id]**

**Command mode:** operational

**Example**
::

	dnRouter# show network-services ipsec counters 1

    Tunnel-ID: 1
        encrypted-packets: 100
        encrypted-octets: 150000
        decrypted-packets: 200
        decrypted-octets: 300000
        encryption-drops: 2
        decryption-drops: 0
        replay-error-dropped-packets: 0
        auth-error-dropped-packets: 0

.. **Help line:** show IPSec tunnel counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
