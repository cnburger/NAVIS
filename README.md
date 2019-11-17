# NAVIS
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
