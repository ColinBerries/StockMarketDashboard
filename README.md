# Stock Market Analysis Dashboard (S.M.A.D.)



Final product
  - In simple terms: Maximize profit
    - Technical analysis and consumer sentiment (news)
      - Technical analysis from the raw data
      - Consumer sentiment from the news
        - Analyzing key words and phrases
    - Short term trades (one month or less)
      - More Data with short term movements, and better   risk management
      - Possibly hedge our positions

# Running the project
Create `backend/.env` based on
`backend/TechnicalAnalysis/.env.example`.

## Backend
Install the necessary modules with the following command:
```bash
pip3 install .
```
Then, start the backend server
```bash
python main.py
```
The backend will start on port 4999

## Frontend
The frontend uses react.
First, install the required node dependencies. Make sure you have [node installed](https://nodejs.org/en) 
```bash
cd ./frontend
```

```bash 
npm start
```
The frontend will start on port 3000

## Backend diagnostic dashboard

The standalone diagnostic dashboard loads EMA, RSI, MACD, OBV,
Accumulation/Distribution, volume, sentiment, tail risk, Hurst, and the
composed portfolio legs directly from the backend modules. It runs separately
from the React application and production API.

Create `backend/.env` with `POLYGON_TOKEN`. Add `NEWS_API_KEY` to enable the
sentiment badge; without it, only that badge reports an error.

From the repository root:

```bash
bash run_dev_dashboard.sh
```

On PowerShell, the equivalent direct command is:

```powershell
Set-Location backend
python dev_dashboard.py
```

Open [http://localhost:5050](http://localhost:5050).



