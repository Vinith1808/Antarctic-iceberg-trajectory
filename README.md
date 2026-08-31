# Antarctic Iceberg Trajectory Prediction

This repository contains the code and resources for predicting Antarctic iceberg trajectories.

## Project Structure

* **`data/`**: Data directory containing raw, interim, processed, and sample datasets.
  * **`raw/`**: Immutable raw datasets (iceberg, ocean, wind, sea_ice). Kept out of version control.
  * **`interim/`**: Intermediate data that has been transformed.
  * **`processed/`**: The final, canonical data sets for modeling.
  * **`samples/`**: Small sample datasets for testing code without loading the full data.
* **`src/`**: Source code for the project.
  * **`data/`**: Scripts to fetch or generate data.
  * **`preprocessing/`**: Scripts to turn raw data into features for modeling.
  * **`physics/`**: Physics-based modeling components.
  * **`ml/`**: Machine learning modeling components.
  * **`uncertainty/`**: Uncertainty quantification logic.
  * **`api/`**: API endpoints (if applicable).
* **`models/`**: Trained and serialized models, model predictions, or model summaries. Checkpoints are ignored in git.
* **`notebooks/`**: Jupyter notebooks for exploration and presentation.
* **`tests/`**: Unit and integration tests.
* **`docs/`**: Project documentation.

## Setup

1. Create a virtual environment: `python -m venv .venv`
2. Activate the virtual environment.
3. Install dependencies: `pip install -r requirements.txt` (once defined).
4. Copy `.env.example` to `.env` and fill in your environment variables.
