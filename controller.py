import sys
from flask import abort
import pymysql as mysql
from config import OPENAPI_AUTOGEN_DIR, DB_HOST, DB_USER, DB_PASSWD, DB_NAME

sys.path.append(OPENAPI_AUTOGEN_DIR)
from openapi_server import models

db = mysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWD, db=DB_NAME)


def get_basins():
    cs = db.cursor()
    cs.execute("SELECT basin_id,ename FROM basin")
    result = [
        models.BasinShort(basin_id, name) for basin_id, name in cs.fetchall()
    ]
    cs.close()
    return result


def get_basin_details(basin_id):
    cs = db.cursor()
    cs.execute(
        """
        SELECT basin_id, ename, area
        FROM basin
        WHERE basin_id=%s
        """, [basin_id])
    result = cs.fetchone()
    cs.close()
    if result:
        basin_id, name, area = result
        return models.BasinFull(basin_id, name, area)
    else:
        abort(404)


def get_stations(basin_id):
    cs = db.cursor()
    cs.execute(
        """
        SELECT station_id, s.ename
        FROM station s
        INNER JOIN basin b ON ST_CONTAINS(b.geometry, POINT(s.lon, s.lat))
        WHERE basin_id=%s
        """, [basin_id])
    result = [
        models.StationShort(station_id, name)
        for station_id, name in cs.fetchall()
    ]
    cs.close()
    return result


def get_station_details(station_id):
    cs = db.cursor()
    cs.execute(
        """
        SELECT s.station_id, b.basin_id, s.ename, s.lat, s.lon
        FROM station s
        INNER JOIN basin b ON ST_CONTAINS(b.geometry, POINT(lon, lat))
        WHERE station_id=%s
        """, [station_id])
    result = cs.fetchone()
    cs.close()
    if result:
        station_id, basin_id, name, lat, lon = result
        return models.StationFull(station_id, basin_id, name, lat, lon)
    else:
        abort(404)


def get_annual_rainfall(basin_id, year):
    cs = db.cursor()
    cs.execute(
        """
        SELECT b.basin_id, r.year, SUM(r.amount) as rainfall
        FROM rainfall r
        INNER JOIN station s ON s.station_id = r.station_id
        INNER JOIN basin b ON ST_CONTAINS(b.geometry, POINT(s.lon, s.lat))
        WHERE basin_id=%s AND year=%s
        GROUP BY r.year, b.basin_id
        """, [basin_id, year])
    result = cs.fetchone()
    cs.close()
    if result:
        basin_id, year, rainfall = result
        return models.RainfallPerYear(basin_id, year, rainfall)
    else:
        abort(404)
