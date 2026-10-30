# Road Accident Hotspot Analysis Using Hadoop MapReduce

A beginner-friendly Distributed Computing project starter.

## What it does
- Stores accident CSV data in HDFS.
- Uses a Python Hadoop Streaming mapper/reducer to aggregate records into geographic grid cells.
- Displays the aggregated cells as a Folium heatmap and hotspot markers in a Streamlit dashboard.
- Includes a small **synthetic demo dataset** only for testing the dashboard before obtaining real data.

## Important data note
`data/demo_accidents_synthetic.csv` is fabricated for testing and is **not real accident data**. Never present its map as real findings.
A community GitHub repository describes an Indian accident CSV with latitude/longitude across seven states:
https://github.com/Aditya2213/INDIAN_ROAD_ACCIDENT_DATASET_DASHBOARD
Inspect its README and dataset provenance before using it in a report; it is not verified here as official government data.
Official Indian MoRTH tables are useful for national/state totals, but generally do not provide accident-level GPS coordinates for a point heatmap:
https://data.opencity.in/dataset/road-accidents-in-india-2024

## Requirements
- Ubuntu Linux (a VM is okay)
- Java JDK compatible with the Hadoop release you install
- Hadoop configured in pseudo-distributed mode
- Python 3
- Python packages: `streamlit pandas folium streamlit-folium plotly`

Hadoop Streaming supports executable scripts as mapper/reducer. See:
https://hadoop.apache.org/docs/stable/hadoop-streaming/HadoopStreaming.html
Hadoop single-node guide:
https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/SingleCluster.html

## Expected dataset schema
CSV must contain `latitude` and `longitude` columns (case-insensitive). Each valid row represents one accident record. Optional columns like city, state, severity, date, hour and casualties can support later extensions.

## Preview the dashboard before Hadoop is installed
Run these commands from this folder:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p outputs
python3 src/local_preview.py data/demo_accidents_synthetic.csv outputs/hotspots.csv
streamlit run src/dashboard.py
```
This preview is only for testing the interface. For your final Distributed Computing demonstration, run the Hadoop job below.

## Hadoop workflow (from the project root on Ubuntu)
1. Put the actual dataset at `data/indian_roads_dataset.csv`.
2. Start Hadoop services as configured in your installation.
3. Create HDFS input directory and upload the CSV:
```bash
hdfs dfs -mkdir -p /road-accidents/input
hdfs dfs -put -f data/indian_roads_dataset.csv /road-accidents/input/accidents.csv
```
4. Locate the Streaming JAR:
```bash
find "$HADOOP_HOME" -name 'hadoop-streaming*.jar'
```
5. Set `STREAMING_JAR` to the path returned by `find`, then run:
```bash
STREAMING_JAR=/path/to/hadoop-streaming-<version>.jar
hdfs dfs -rm -r -f /road-accidents/output
mapred streaming   -files src/mapper.py,src/reducer.py   -input /road-accidents/input/accidents.csv   -output /road-accidents/output   -mapper "python3 mapper.py"   -reducer "python3 reducer.py"
```
If your Hadoop release requires an explicit JAR invocation, follow that release's official Streaming documentation.
6. Download the reducer output:
```bash
mkdir -p outputs
hdfs dfs -get -f /road-accidents/output/part-00000 outputs/part-00000
python3 src/format_hadoop_output.py outputs/part-00000 outputs/hotspots.csv
```
7. Launch:
```bash
streamlit run src/dashboard.py
```

## What the MapReduce job does
- Mapper: rounds each valid latitude/longitude to a 0.01-degree grid cell and emits `grid_lat,grid_lon<TAB>1`.
- Hadoop shuffle/sort groups identical cells.
- Reducer: sums accident records per cell.
- A grid count is a concentration in the dataset, not proof that a location is inherently dangerous. Data coverage and GPS quality matter.

## 5–7 minute demonstration
1. Show the CSV and GPS columns.
2. Show the file in HDFS: `hdfs dfs -ls /road-accidents/input`.
3. Run the Streaming job and show job progress.
4. Show reducer output in HDFS.
5. Open the dashboard and display the heatmap and hotspot ranking.
6. Explain: HDFS stores the data; MapReduce aggregates geographic cells; Folium visualizes the reducer output.

## Suggested report title
**Distributed Road Accident Hotspot Analysis Using Hadoop MapReduce**

## Honest limitations
- A single-node pseudo-distributed setup demonstrates Hadoop components but is not a physical multi-node cluster.
- Hotspot findings depend on dataset provenance and GPS accuracy.
- High record counts show concentrations in the dataset; they do not establish causes or predict future crashes.
