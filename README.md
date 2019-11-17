# NAVIS (Nautical AIS Visualisation System)
An Automatic Identification System Visualization Framework

## What is NAVIS?
NAVIS is an open-source AIS data visualisation framework. It was created to make the visualisation of spatial-temporal AIS data easier.
This framework presented was created to visualise raw AIS data as well as data generrated by algorithms.
This tool visualises the trajectory of AIS data, an can be used to easy visualise trajectories of vessels.

## What is AIS data?
AIS data is a combination of terrestrial (T-AIS) messages that are continuously collected by onshore receiving stations and satellite AIS messages (S-AIS) arriving in bursts when satellites transfer buffered data onto a ground station.

## What type of visualisations does NAVIS do?
- Static map of up to three vessels
- Animation of a vessel
- Spatial distribution map

## How to use NAVIS?
NAVIS has a Graphical UserInterface (GUI) to work with. NAVIS works with any database, but the code that is on GitHub makes use of PostgreSQL. One connects to a database with the following structure: MMSI, Longitude, Latitude, sog, rot, cog, trueheading, msgtype, msgsource, datetime. In PostgreSQL, the longitude and latetide should be of the type "geom".

## YouTube Video of NAVIS:
A video of NAVIS in action can be seen [here](https://www.youtube.com/watch?v=FfBeTMqRXUw&feature=youtu.be).

# Getting NAVIS up and running:
## Compatability:
Windows 10
Ubuntu (coming soon)

## What to install?
### Python Related software
- [Python 3](https://www.python.org/downloads/)
- [Numpy](https://numpy.org/)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/users/installing.html) & [Basemap](https://matplotlib.org/basemap/)

If you are struggling to install Basemap please make use of this YouTube [tutorial](https://youtu.be/mXR47qiTdWQ)

### To save a .mkv video file
- [FFMpeg](https://www.ffmpeg.org/download.html)
### Database tools
- [Psycopg](http://initd.org/psycopg/download/)
- [PostgreSQL](https://www.postgresql.org/download/) & [PostGIS](https://postgis.net/install/)
- [SQLAlchemy](https://www.sqlalchemy.org/download.html)
