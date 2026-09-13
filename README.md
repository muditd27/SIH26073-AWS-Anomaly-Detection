# SkyGuard AI

Streamlit dashboard from the SkyGuard / Nexora mockups.

## Run locally

```bash
cd skyguard-ai
python -m pip install -r requirements.txt
streamlit run app.py
```

- `stations_page.py` is the home grid (AWS001–AWS004)
- Click any station card to open `?station=AWS001`
- `station_detail.py` is the selected-station view
- Home icon and breadcrumb return to the station list
