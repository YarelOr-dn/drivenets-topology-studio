show ldp neighbors detail- N/A for this version
-----------------------------------------------

**Command syntax: show ldp neighbors detail**

**Description:** Displays detailed information on LDP neighbors including session message statistics.

**CLI example:**
::

	
	dnRouter# show ldp neighbors detail
	Peer LDP Identifier: 10.99.1.66:0
	  TCP connection: 3.3.3.9:646 - 10.99.1.66:35464
	  Session Holdtime: 30 sec
	  State: OPERATIONAL; Downstream-Unsolicited
	  Up time: 00:01:00
	  LDP Sync: Converged
	  Graceful restart:
	    Local - Restart: disabled, Helper mode: disabled
	    Remote - Restart: disabled, Helper mode: disabled
	  LDP Discovery Sources:
	    IPv4:
	      Interface: bundle-20.2005
	
	  Message Statistics:                Sent              Rcvd
	  ------------------            ---------         ---------
	      Initialization                   66                66
	      Address                          66                66
	      Address-Withdraw                  0                 0
	      Label-Mapping                   119                66
	      Label-Withdraw                   40                 0
	      Label-Release                     0                37
	      Label-Request                     0                 0
	      Label-Abort-Request               0                 0
	      Notification                      1                64
	      KeepAlive                       591               610
	      Total                           883               909
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:**
