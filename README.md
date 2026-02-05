# 💰 YouTube Affiliate Offer Finder

Find the most profitable affiliate offers for your YouTube channel by aggregating data from multiple affiliate networks.

## Features

- 🔍 Search across multiple affiliate networks (Impact, CJ, Awin, Partnerstack)
- 📊 Unified view of offers with key metrics (EPC, commission, conversion rate)
- 🎯 YouTube-specific scoring algorithm
- 🌐 Clean web interface built with Streamlit
- 📥 Export results to CSV

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:

```bash
# Impact API Credentials
IMPACT_ACCOUNT_SID=your_account_sid_here
IMPACT_AUTH_TOKEN=your_auth_token_here
```

#### How to Get Impact API Credentials

1. Log into your Impact account: https://app.impact.com
2. Go to **Settings** → **API**
3. Generate API credentials (Account SID + Auth Token)
4. Copy them to your `.env` file

### 3. Run the Application

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Test Connection**: Click "Test Connections" in the sidebar to verify your API credentials
2. **Search Offers**:
   - Enter a keyword (e.g., "VPN", "hosting", "software")
   - Adjust filters (min YouTube score, EPC, commission)
   - Click "Search Offers"
3. **Review Results**: Offers are ranked by YouTube suitability score
4. **Export**: Download results as CSV for further analysis

## YouTube Scoring Algorithm

Each offer gets a score (0-100) based on:

- **EPC (40 points)**: Higher earnings per click = better for video promotion
- **Commission (30 points)**: Higher payouts make promotion worthwhile
- **Popularity (30 points)**: Proven offers convert better

Scores 80+ are excellent for YouTube, 60-79 are good, below 60 may need evaluation.

## Supported Networks

| Network | Status | API Docs |
|---------|--------|----------|
| **Impact** | ✅ Implemented | [API Docs](https://developer.impact.com/) |
| **CJ (Commission Junction)** | 🚧 Coming Soon | [API Docs](https://developers.cj.com/) |
| **Awin** | 🚧 Coming Soon | [API Docs](https://wiki.awin.com/index.php/API) |
| **Partnerstack** | 🚧 Coming Soon | [API Docs](https://docs.partnerstack.com/) |

## Project Structure

```
affiliate-offer-finder/
├── app/
│   ├── main.py              # Streamlit web app
│   ├── config.py            # API credential management
│   ├── networks/
│   │   ├── base.py          # Base network interface
│   │   └── impact.py        # Impact API integration
│   ├── models/
│   │   └── offer.py         # Unified offer data model
│   └── services/
│       └── aggregator.py    # Multi-network aggregation
├── .env                     # API credentials (git-ignored)
├── .env.example             # Template for credentials
├── requirements.txt         # Python dependencies
└── README.md
```

## Adding More Networks

To add a new network (CJ, Awin, etc.):

1. Create `app/networks/{network_name}.py`
2. Extend `BaseNetwork` class
3. Implement `search_offers()`, `get_offer_details()`, `test_connection()`
4. Add credentials to `config.py`
5. Import in `aggregator.py`

## Troubleshooting

**"No networks configured" error**
- Make sure you've created a `.env` file (copy from `.env.example`)
- Add your API credentials to `.env`

**API connection fails**
- Verify credentials are correct
- Check if your affiliate account has API access enabled
- Some networks require manual approval for API access

**No offers found**
- Try broader search terms
- Lower the minimum filters (EPC, YouTube score)
- Check if your account has approved campaigns

## License

MIT License - feel free to use and modify for your needs.
