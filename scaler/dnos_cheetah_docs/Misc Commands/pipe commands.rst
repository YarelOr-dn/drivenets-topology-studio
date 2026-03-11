pipe commands
-------------

**Minimum user role:** viewer

Pipe commands filter the output of show commands. The supported pipe commands are:

no-more: show all CLI output without the "more" option.

include: filter the results that include a requested parameter (whole word or part of a word). Can be used in combination with "leading [value]" or "trailing [value]" to provide context (up to 1000 lines) for the match:

- trailing <num> - Print the number of lines of trailing context after the matching line.

- leading <num> - Print the number of lines of leading context before the matching line.

find - The first occurrence of the object treated. The command will “find” the first line in the output that meets the criteria and display all of the output until the end of. The operator can use trailing, leading or both for any given “find”. The maximum number of lines to be found for leading and trailing is limited to 1000. The regex option can be combined in find. Match is case-insensitive. To run a case-sensitive match, use "case-sensitive" after <text>.

exclude: filter the results that exclude the requested parameter (whole word or part of a word).

case-sensitive: By default, all pattern match are case-insensitive, to run a case-sensitive match, use "case-sensitive" after <text> for "include", "exclude", "find" request, including "regex" option.

regex: filter the results using regular expression. Can be used with include , exclude or find commands.

display-headers: use for displaying table headers. By default, the table headers are not displayed when using pipe commands.

monitor: an augmented flag to show command for displaying CLI output at regular intervals. The command output is refreshed compared to the previous output at regular configured intervals. The filters are applied to the entries only, not including the table headers.

You can use the monitor command in combination with the following commands:

- interval: set the interval time (in seconds) between CLI command output refreshes. Range: 1..3600 seconds; Default: 3

- diff: highlights the difference from the previous CLI command output refresh.

count: count and display the number of lines in the output. The count option should be the last pipe, and will count the output lines after all other filtering options such as include/exclude/regex. There may be 3 pipes combined and the output will show the total number of lines. An empty output will result in 0 lines.

tail - The command will show the last <num> of lines from the file. If <num> is not provided, the last 100 lines will be displayed by default.

The pipe command follows the show command and is separated by the pipe character (|). Pipe commands can be concatenated to further filter the displayed output:

**Command syntax: show** parameter [parameter-value] **\| pipe-command** \| pipe-command .

**Command mode:** operational

**Example**

The pipe commands are demonstrated here on the show interfaces ip command. The following is the output of this command without any pipe command:

::

	dnRouter# show interfaces ip | monitor
	dnRouter# show interfaces ip | no-more
	dnRouter# show interfaces ip | include [value]
	dnRouter# show interfaces ip | include regex [value]
	dnRouter# show interfaces ip | exclude [value]
	dnRouter# show interfaces ip | exclude regex [value]
	dnRouter# show interfaces ip | include [value] display-headers
	dnRouter# show interfaces ip | find "[value]" trailing [value] leading [value]
	dnRouter# show interfaces ip | tail [value]
	dnRouter# show interfaces ip | count

	dnRouter# show interfaces ip | include down trailing 1
	dnRouter# show interfaces ip | include down trailing 1 leading 4

	dnRouter# show interfaces ip

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down 	   | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | find "ge100"

	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down 	   | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | find "bundle" trailing 2 | tail 1

	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |

	dnRouter# show interfaces ip | find "lo1" leading 2

	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down 	   | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | include bundle-3 display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |

	dnRouter# show rsvp tunnels | include To-XRV1 case-sensitive

	1.1.1.1         5.5.5.5         head     down    -       -        2h45m36s         To-XRV1


	dnRouter# show interfaces ip | include bundle-3 | count

	lines: 2

	dnRouter# show interfaces ip | include bundle-3 display-headers | count

	lines: 4

	dnRouter# show interfaces ip | include regex ge\d+ display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |

	dnRouter# show interfaces ip | include bundle-3 | include abcd display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |

	dnRouter# show interfaces ip | include bundle-3 | exclude abcd display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |


	dnRouter# show interfaces ip | include regex bundle-3|abcd display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |

	dnRouter# show interfaces ip | include regex bundle-3|abcd

	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |

	dnRouter# show interfaces ip | exclude bundle-3 display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | exclude regex ge\d+ display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | exclude regex bundle-3|ge100 display-headers

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | exclude regex bundle-3|ge100

	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | monitor

	Every 3s: show interfaces ip                                               2020-01-23 16:08:27

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	dnRouter# show interfaces ip | monitor

	Every 3s: show interfaces ip                                               2020-01-23 16:08:27

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | up          | 30.4.4.1/30    | 1006:abcd:12::2/128            |
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |

	Press CTRL+C to quit

	dnRouter# show interfaces ip | monitor interval 10 diff

	Every 10s: show interfaces ip                                              2020-01-23 16:08:27

	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| bundle-3        | enabled  | up          | 30.1.1.1/30    | 2001:1234::1/122               |
	| bundle-3.200    | enabled  | down        | 30.4.4.1/30    | 1006:abcd:12::2/128            |
	| ge100-2/1/1     | disabled | down        | 30.2.2.1/30    | 1001:abcd:12::2/128            |
	| ge100-2/1/1.100 | enabled  | up          |                |                                |
	| ge100-3/1/1     | enabled  | up          |                |                                |
	| lo1             | disabled | down        | 1.1.1.1/32     | 2001::0001:0001:0001:0001/128  |


	Press CTRL+C to quit

	dnRouter# show interfaces ip | include down trailing 1
	| bundle-263.1264      | disabled | down            | 1.12.51.0/31       | 2001:12:51::/127                            |
	| bundle-263.2702      | enabled  | up              | 6.12.90.0/31       | 2006:12:90::/127                            |
	--
	| bundle-1112          | enabled  | down            | 1.11.12.1/31       | 2001:11:12::1/127                           |
	| bundle-1213          | enabled  | down            | 1.12.13.0/31       | 2001:12:13::/127                            |
	| bundle-1215          | disabled | down            | 1.12.15.0/31       | 2001:12:15::/127                            |
	| bundle-1216          | enabled  | up              | 1.12.16.0/31       | 2001:12:16::/127                            |
	--
	| bundle-1230          | disabled | down            | 1.12.30.0/31       | 2001:12:30::/127                            |
	| ge10-0/0/11/0        | disabled | down            |                    |                                             |
	| ge10-0/0/11/1        | enabled  | down            |                    |                                             |
	| ge10-0/0/11/2        | enabled  | down            |                    |                                             |
	| ge10-0/0/11/3        | enabled  | down            |                    |                                             |
	| ge100-0/0/0          | enabled  | down            |                    |                                             |
	| ge100-0/0/1          | enabled  | down            |                    |                                             |
	| ge100-0/0/2          | disabled | down            |                    |                                             |
	| ge100-0/0/3          | disabled | down            |                    |                                             |
	| ge100-0/0/4          | enabled  | down            |                    |                                             |
	| ge100-0/0/5          | enabled  | down            |                    |                                             |
	| ge100-0/0/6          | enabled  | down            |                    |                                             |
	| ge100-0/0/7          | enabled  | down            |                    |                                             |
	| ge100-0/0/8          | enabled  | down            |                    |                                             |
	| ge100-0/0/9          | disabled | down            |                    |                                             |
	| ge100-0/0/10         | disabled | down            |                    |                                             |
	| ge100-0/0/11         | disabled | not-present     |                    |                                             |

	dnRouter# show interfaces ip | include down trailing 1 leading 4
	| bundle-252.1348      | enabled  | up              | 5.12.93.246/31     | 2005:12:93::f6/127                          |
	| bundle-252.1349      | enabled  | up              | 5.12.93.248/31     | 2005:12:93::f8/127                          |
	| bundle-253           | enabled  | up              |                    |                                             |
	| bundle-263           | enabled  | up              |                    |                                             |
	| bundle-263.1264      | disabled | down            | 1.12.51.0/31       | 2001:12:51::/127                            |
	| bundle-263.2702      | enabled  | up              | 6.12.90.0/31       | 2006:12:90::/127                            |
	--
	--
	| bundle-263.2702      | enabled  | up              | 6.12.90.0/31       | 2006:12:90::/127                            |
	| bundle-263.2703      | enabled  | up              | 7.12.90.0/31       | 2007:12:90::/127                            |
	| bundle-1112          | enabled  | down            | 1.11.12.1/31       | 2001:11:12::1/127                           |
	| bundle-1213          | enabled  | down            | 1.12.13.0/31       | 2001:12:13::/127                            |
	| bundle-1215          | disabled | down            | 1.12.15.0/31       | 2001:12:15::/127                            |
	| bundle-1216          | enabled  | up              | 1.12.16.0/31       | 2001:12:16::/127                            |
	--
	--
	| bundle-1216          | enabled  | up              | 1.12.16.0/31       | 2001:12:16::/127                            |
	| bundle-1218          | enabled  | up              | 1.12.18.0/31       | 2001:12:18::/127                            |
	| bundle-1230          | disabled | down            | 1.12.30.0/31       | 2001:12:30::/127                            |
	| ge10-0/0/11/0        | disabled | down            |                    |                                             |
	| ge10-0/0/11/1        | enabled  | down            |                    |                                             |
	| ge10-0/0/11/2        | enabled  | down            |                    |                                             |
	| ge10-0/0/11/3        | enabled  | down            |                    |                                             |
	| ge100-0/0/0          | enabled  | down            |                    |                                             |
	| ge100-0/0/1          | enabled  | down            |                    |                                             |
	| ge100-0/0/2          | disabled | down            |                    |                                             |
	| ge100-0/0/3          | disabled | down            |                    |                                             |
	| ge100-0/0/4          | enabled  | down            |                    |                                             |
	| ge100-0/0/5          | enabled  | down            |                    |                                             |
	| ge100-0/0/6          | enabled  | down            |                    |                                             |
	| ge100-0/0/7          | enabled  | down            |                    |                                             |
	| ge100-0/0/8          | enabled  | down            |                    |                                             |
	| ge100-0/0/9          | disabled | down            |                    |                                             |
	| ge100-0/0/10         | disabled | down            |                    |                                             |
	| ge100-0/0/11         | disabled | not-present     |                    |                                             |

**Command History**

+---------+------------------------------------------------------------------+
| Release | Modification                                                     |
+=========+==================================================================+
| 5.1.0   | Command introduced                                               |
+---------+------------------------------------------------------------------+
| 9.0     | Updated available pipe commands                                  |
+---------+------------------------------------------------------------------+
| 11.5    | Added ability to display table-headers                           |
+---------+------------------------------------------------------------------+
| 13.2    | Updated available pipe commands                                  |
+---------+------------------------------------------------------------------+
| 13.3    | Added leading and trailing options for "include" pipe operations |
+---------+------------------------------------------------------------------+
| 18.2    | Updated support for regex match for find                         |
|         | Updated support for case-sensitive match for regex usage         |
+---------+------------------------------------------------------------------+
