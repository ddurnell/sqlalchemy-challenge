import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc, text
from datetime import datetime as dt
import numpy as np
import pandas as pd
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


# #################################################
# # Flask Routes
# #################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/><br/>"
        f"Use tstats to enter a start and end date (optional) in the form 'yyy-mm-dd'<br/>"
        f"example: /api/v1.0/tstats/2017-07-10 or /api/v1.0/tstats/2012-07-10/2017-07-15<br/>"
        f"/api/v1.0/tstats<br/>"
    )

# A query to retrieve the last 12 months of precipitation data
# It returns a dictionary
def precip_query():
    # Calculate the date 1 year ago from the last data point in the database
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    last_date = session.query(Measurement.date, Measurement.prcp).\
        order_by(desc(Measurement.date)).all()[0][0]

    ldate = dt.strptime(last_date, '%Y-%m-%d').date()
    #print(ld)
    ly = ldate.year
    lm = ldate.month
    ld = ldate.day

    fy = ly - 1
    fd = dt(fy, lm, ld)

    ld_str = ldate.strftime('%Y-%m-%d')
    fd_str = fd.strftime('%Y-%m-%d')

    last_year = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date < ldate).\
        filter(Measurement.date > fd)
    
    session.close()

    df = pd.read_sql(last_year.statement, session.bind)
    dfd = df.set_index('date')
    dfd = dfd.dropna()
    dfd = dfd.sort_index()
    dfd.head()
    return dfd.to_dict()

# A query to retrieve the last 12 months of temperature data
# It returns a dictionary
# TODO: combine this with precip_query. It is almost the same.
def temp_query():
    # Calculate the date 1 year ago from the last data point in the database
    
    # Create our session (link) from Python to the DB
    session = Session(engine)

    last_date = session.query(Measurement.date, Measurement.tobs).\
        order_by(desc(Measurement.date)).all()[0][0]

    ldate = dt.strptime(last_date, '%Y-%m-%d').date()
    #print(ld)
    ly = ldate.year
    lm = ldate.month
    ld = ldate.day

    fy = ly - 1
    fd = dt(fy, lm, ld)

    ld_str = ldate.strftime('%Y-%m-%d')
    fd_str = fd.strftime('%Y-%m-%d')

    last_year = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date < ldate).\
        filter(Measurement.date > fd)
    
    session.close()

    df = pd.read_sql(last_year.statement, session.bind)
    dfd = df.set_index('date')
    dfd = dfd.dropna()
    dfd = dfd.sort_index()
    dfd.head()
    return dfd.to_dict()


# Returns a dictionary of dates and precipitation values
@app.route("/api/v1.0/precipitation")
def precipitation():
    df = precip_query()
    return jsonify(df)

# Returns list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Get the station name, latitude, longitude, and elevation
    # Get a dataframe of the stations data
    stations = session.query(Station.station,\
                            Station.name,\
                            Station.latitude,\
                            Station.longitude,\
                            Station.elevation
                            )
    session.close()
    st_df = pd.DataFrame(stations)

    return jsonify(st_df.to_dict(orient="records"))

#Returns a list of dates and temperature observations for the previous year.
@app.route("/api/v1.0/tobs")
def tobs():
    df = temp_query()
    return jsonify(df)

# Returns a list of the minimum temperature, the average temperature, and the max temperature
#  for a given start or start-end range.
@app.route("/api/v1.0/tstats/<start>")
@app.route("/api/v1.0/tstats/<start>/<end>")
def tstats(start, end = ""):
    if end == "":
        now = dt.today()
        end = now.strftime("%Y-%m-%d")

    # Create our session (link) from Python to the DB
    session = Session(engine)

    r = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    session.close()

    return jsonify(r)

if __name__ == '__main__':
    app.run(debug=True)
