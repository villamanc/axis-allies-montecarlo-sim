# ⚔️ Axis & Allies Combat Simulator - Streamlit App

A web-based combat simulator for Axis & Allies board game battles. Run thousands of simulations to analyze battle outcomes with detailed statistics and visualizations.

## Features

- 🎲 Simulate up to 50,000 battles
- 📊 Comprehensive statistical analysis
- 📈 6 detailed visualization charts
- 🔄 Support for all unit types (land, air, sea)
- 🎯 Round-by-round breakdowns
- 📱 Responsive web interface

## Quick Start (Local)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
streamlit run combat_simulator_app.py
```

3. **Open your browser:**
The app will automatically open at `http://localhost:8501`

## Deploying to Streamlit Cloud

1. **Push to GitHub:**
   - Create a new GitHub repository
   - Upload `combat_simulator_app.py` and `requirements.txt`

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file path: `combat_simulator_app.py`
   - Click "Deploy"

3. **Share:**
   - Your app will be live at: `https://[your-app-name].streamlit.app`

## How to Use

1. **Configure Forces:**
   - Use the left column to set up attacker units
   - Use the right column to set up defender units
   - Each unit shows its attack/defense values

2. **Adjust Settings:**
   - Set number of simulations (more = more accurate)
   - Enable/disable random seed for reproducibility

3. **Run Simulation:**
   - Click "Run Combat Simulation"
   - View instant results with charts and statistics

4. **Analyze Results:**
   - Check win rates for each side
   - Review detailed round-by-round statistics
   - Examine 6 comprehensive charts

## Combat Values

Default Axis & Allies 1942 Second Edition values:

**Land Units:**
- Infantry: Attack 1, Defense 2
- Artillery: Attack 2, Defense 2
- Mechanized Infantry: Attack 1, Defense 2
- Tank: Attack 3, Defense 3
- AAA: Attack 0, Defense 1

**Air Units:**
- Fighter: Attack 3, Defense 4
- Bomber: Attack 4, Defense 1

**Sea Units:**
- Submarine: Attack 2, Defense 2
- Destroyer: Attack 3, Defense 3
- Cruiser: Attack 3, Defense 3
- Battleship: Attack 4, Defense 4
- Aircraft Carrier: Attack 1, Defense 3
- Transport: Attack 0, Defense 1

## Charts Explained

1. **Battle Outcomes** - Pie chart showing win distribution
2. **Average Units Surviving** - Line chart tracking unit attrition
3. **Average Hits Scored** - Bar chart comparing damage output
4. **When Each Side Was Eliminated** - Histogram of elimination timing
5. **Combat Duration Distribution** - Overall battle length statistics
6. **Cumulative Win Probability** - Progressive win chances by round

## Tips

- Start with 10,000 simulations for good balance of speed/accuracy
- Use random seed for comparing different army compositions
- Expand round-by-round details for deep analysis
- Compare different force configurations to optimize strategy

## Technical Details

- Built with Streamlit for web interface
- NumPy/Pandas for efficient simulation
- Matplotlib/Seaborn for visualizations
- Vectorized operations for performance

## License

Free to use and modify for personal/educational purposes.
