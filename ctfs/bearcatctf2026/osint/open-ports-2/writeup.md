---
author: Fenix
credit: Fenix, Grok
---
## Solution

This challenge is basically the same as the previous challenge, but with a different ship
and further back in time. (2009)

As its data only went back to 2012, I couldn't use 
[the tool I used on the previous challenge](https://globalfishingwatch.org/map/vessel-search).
Instead, I repeatedly prompted grok to find me a dataset that would contain location until it found the following data from NOAA:

- [https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone14_2009_01.zip](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone14_2009_01.zip)

- [https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone15_2009_01.zip](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone15_2009_01.zip)

- [https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone16_2009_01.zip](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone16_2009_01.zip)

- [https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone17_2009_01.zip](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2009/01_January_2009/Zone17_2009_01.zip)

I then asked it to write a script to parse through this data looking for an MMSI of 311714000 and the script outputted this:
```
🚢 FINAL FIXED ANALYSIS for MMSI 311714000 — January 2009
📂 Loading Zone14_2009_01.gdb ...
📂 Loading Zone15_2009_01.gdb ...
📂 Loading Zone16_2009_01.gdb ...
   → 1,313 positions loaded
📂 Loading Zone17_2009_01.gdb ...
   → 329 positions loaded
📅 Daily AIS transmissions in January 2009:
BaseDateTime
2009-01-19 329
2009-01-21 371
2009-01-22 466
2009-01-23 74
2009-01-24 232
2009-01-25 170
Name: count, dtype: int64
================================================================================
📍 POSITIONS ON 2009-01-19 (329 records)
================================================================================
       BaseDateTime LAT LON SOG
2009-01-19 01:20:00 23.418323 -80.300763 13
2009-01-19 01:23:00 23.421817 -80.314238 12
2009-01-19 01:29:00 23.427473 -80.335742 12
2009-01-19 01:30:00 23.428467 -80.339355 12
2009-01-19 01:32:00 23.429723 -80.344145 12
2009-01-19 01:33:00 23.431008 -80.348903 12
   ...
       BaseDateTime LAT LON SOG
2009-01-19 12:06:00 23.997322 -82.284318 9
2009-01-19 12:18:00 24.005447 -82.314313 8
2009-01-19 19:12:00 24.342843 -83.228853 8
2009-01-19 19:25:00 24.363888 -83.251475 9
2009-01-19 19:26:00 24.366242 -83.254135 9
2009-01-19 22:29:00 24.769867 -83.586037 10
================================================================================
📍 POSITIONS ON 2009-01-21 (371 records)
================================================================================
       BaseDateTime LAT LON SOG
2009-01-21 17:22:00 29.579273 -87.575332 13
2009-01-21 17:24:00 29.585702 -87.580430 13
2009-01-21 17:28:00 29.595903 -87.588558 13
2009-01-21 17:29:00 29.598802 -87.590835 13
2009-01-21 17:30:00 29.602712 -87.593920 13
2009-01-21 17:31:00 29.605673 -87.596237 13
   ...
       BaseDateTime LAT LON SOG
2009-01-21 23:53:00 30.700222 -88.037832 3
2009-01-21 23:54:00 30.701058 -88.037983 3
2009-01-21 23:55:00 30.701707 -88.038142 2
2009-01-21 23:57:00 30.702238 -88.038232 2
2009-01-21 23:58:00 30.702828 -88.038370 2
2009-01-21 23:59:00 30.703408 -88.038552 2
💾 All data saved to MMSI_311714000_Jan2009_FINAL.csv
✅ Run complete!
Now copy-paste the LAT/LON pairs from 2009-01-19 or 2009-01-21 here.
I'll reverse-geocode them and tell you the exact nearest city/port/anchorage.
```

I then pasted the coordinates into google maps and saw that the nearest major city was Mobile, Alabama.

## Flag
`BCCTF{Mobile}`
