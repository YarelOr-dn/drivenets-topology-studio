show pim neighbors detail
-------------------------

**Minimum user role:** viewer

You can use this command to display the local router and PIM peer router neighbors information status.



**Command syntax: show pim neighbors detail** interface [interface-name]

**Command mode:** operational



**Parameter table**

+----------------+-----------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter      | Description                                                           | Range                                              | Default |
+================+=======================================================================+====================================================+=========+
| interface-name | The name of the local router and PIM peer router neighbor information | lo<0-65535>                                        | none    |
|                |                                                                       | ge{100/400}-X/Y/Z                                  |         |
|                |                                                                       | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |         |
|                |                                                                       | bundle-<bundle-id>                                 |         |
|                |                                                                       | bundle-<bundle-id.sub-bundle-id>                   |         |
+----------------+-----------------------------------------------------------------------+----------------------------------------------------+---------+

**Example**
::

    dnRouter# show pim neighbors detail

    PIM neighbors:

    Interface: bundle-20.222

    This Router:
    Address: 12.1.6.1,  (S,G) Join Count: 0, ( *, G) Join Count: 1
        Hello Holdtime Option: 105 seconds. Remaining 43
        Hello DR Priority Option: 1
        Hello GenID Option: 3001392933
        Elected DR: No
        Rx Join: Group           Source          Timeout
                 231.1.1.1           *               203

    PIM Peer Routers:
    Address: 12.1.6.2
        Hello Holdtime Option: 105 seconds.
        Hello DR Priority Option: 1
        Hello GenID Option: 3001444967
        Elected DR : Yes

    Interface: bundle-1

    This Router:
    Address: 12.2.6.21,  (S,G) Join Count: 0, ( *, G) Join Count: 0
        Hello Holdtime Option: 105 seconds. Remaining 42
        Hello DR Priority Option: 1
        Hello GenID Option: 2301392933
        Elected DR: No
        Rx Join: Group           Source          Timeout

    PIM Peer Routers:
    Address: 12.2.6.22
        Hello Holdtime Option: 105 seconds.
        Hello DR Priority Option: 1
        Hello GenID Option: 3401444967
        Elected DR: Yes

    Interface: ge100-1/1/0

    This Router:
    Address: 13.3.6.14, (S,G) Join Count: 0, ( *, G) Join Count: 0
        Hello Holdtime Option: 105 seconds. Remaining 12
        Hello DR Priority Option: 1
        Hello GenID Option: 3388392943
        Elected DR: Yes
        Rx Join: Group           Source          Timeout

    PIM Peer Routers:
    Address: 13.3.6.13
        Hello Holdtime Option: 105 seconds.
        Hello DR Priority Option: 1
        Hello GenID Option: 3432123456
        Elected DR: No

    Interface: ge400-1/1/10.1

    This Router:
    Address: 15.1.7.33, (S,G) Join Count: 0, ( *, G) Join Count: 0
        Hello Holdtime Option: 105 seconds. Remaining 98
        Hello DR Priority Option: 1
        Hello GenID Option: 3321392943
        Elected DR: No
        Rx Join: Group           Source          Timeout

    PIM Peer Routers:
    Address: 15.1.7.34
        Hello Holdtime Option: 105 seconds.
        Hello DR Priority Option: 1
        Hello GenID Option: 4321123456
        Elected DR: Yes

    dnRouter# show pim neighbors detail interface bundle-20.222

    PIM neighbors:

    Interface: bundle-20.222

    This Router:
    Address: 12.1.6.1,  (S,G) Join Count: 0, ( *, G) Join Count: 1
        Hello Holdtime Option: 105 seconds. Remaining 42
        Hello DR Priority Option: 1
        Hello GenID Option: 3001392933
        Elected DR: No
        Rx Join: Group           Source          Timeout
                 231.1.1.1       *                 203

    PIM Peer Routers:
    Address: 12.1.6.2
        Hello Holdtime Option: 105 seconds.
        Hello DR Priority Option: 1
        Hello GenID Option: 3001444967
        Elected DR: Yes

.. **Help line:** Show PIM neighbors detailed information

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
