I wrote this thing as a gimmick for a conference to show how much information some mobile devices leak over wifi.
People asked for the source code, so here it is. Enjoy!

*warning*: there are vulns!

Usage
=====

1. Plug in as many wifi dongles as you can. The scripts do not channel hop, but instead prioritizes popular channels. Due to channel overlap, 5 interfaces **should** cover the entire 2.4GHz band.
2. Run `./maclogger.py`
3. Open new terminal, cd to vicinity/
4. Run `watch -n 1 --color ./vicinity.py`

