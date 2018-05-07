I wrote this thing as a gimmick for a conference to show how much information some mobile devices leak over wifi.
People asked for the source code, so here it is. Enjoy!

**warning**: there are vulns!


What is it?
===========

It's a tool that shows you (real time) which wifi clients that are nearby, and which network they are searching for (probe requests).
It shows you something like this:

```
[strength] [mac]        [oui]         [seen]
-53 aa:bb:cc:dd:ee:ff   Manufacturer  7s ago
  (Probe request) -53   seen 6s ago:  NETGEAR71
  (Probe request) -53   seen 6s ago:  Starbucks
  (Probe request) -53   seen 6s ago:  eduroam
  (Probe request) -53   seen 6s ago:  Tivoli Hotel & Congress Center
  (Probe request) -53   seen 6s ago:  FREEWIFI_OLEARYS
  (Probe request) -53   seen 6s ago:  hideyokidshideyowifi
```
...

Usage
=====

1. Plug in as many wifi dongles as you can. The scripts do not channel hop, but instead prioritizes popular channels. Due to channel overlap, 5 interfaces *should* cover the entire 2.4GHz band.
2. Run `./maclogger.py`
3. Open new terminal, cd to vicinity/
4. Run `watch -n 1 --color ./vicinity.py`


PRs are welcome!
