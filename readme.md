# British Auction in RFQ System

A simplified RFQ system with British-auction bidding: automatic time extensions, a hard forced-close, configurable triggers, and a full activity log.

**Stack:** Django 5 + Django REST Framework (SQLite by default, MySQL optional) and React (Vite).

## Folder structure
```
british-auction/
├── README.md
├── HLD_and_Schema.md            # architecture diagram (Mermaid), bid flow, DB schema
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                  # settings, root urls, wsgi
│   └── auction/
│       ├── models.py            # Supplier, RFQ, Bid, ActivityLog
│       ├── services.py          # ranking + place_bid (locking, extension rules)
│       ├── serializers.py       # validation + response shaping
│       ├── views.py, urls.py    # REST endpoints
│       ├── migrations/
│       └── management/commands/seed_demo.py
└── frontend/
    ├── package.json, vite.config.js, index.html
    └── src/ main.jsx, App.jsx (listing, details, forms), api.js, styles.css
```

## Run it
**Backend** (http://localhost:8000)
```
cd backend
pip install -r requirements.txt     # mysqlclient only needed for MySQL
python manage.py migrate
python manage.py seed_demo          # optional demo auction
python manage.py runserver
python manage.py test               # run the tests
```
MySQL: set `DB_ENGINE=mysql DB_NAME=... DB_USER=... DB_PASSWORD=... DB_HOST=...`. Use MySQL to see real row-lock behaviour; SQLite ignores `select_for_update`.

**Frontend** (http://localhost:5173)
```
cd frontend
npm install
npm run dev
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/rfqs/` | Listing: name/ID, lowest bid, close time, forced close, status |
| POST | `/api/rfqs/` | Create RFQ with British auction config (X, Y, trigger) |
| GET | `/api/rfqs/{id}/` | Details: bids with ranks (L1, L2...), quote details, config, activity log |
| POST | `/api/rfqs/{id}/bids/` | Submit a quote |

## Rules implemented
- Forced close must be later than bid close (API validation + DB CHECK constraint).
- An extension never goes past forced close: `new_close = min(close + Y, forced_close)`.
- Triggers (only inside the last X minutes before close): `ANY_BID`, `ANY_RANK_CHANGE`, `L1_CHANGE`.
- Every bid and every extension (with its reason) is written to the activity log.
- Status is computed on read: Upcoming / Active / Closed / Force Closed.

## Design decisions & assumptions
- **Concurrency:** each bid runs in a transaction holding a row lock on the RFQ, so bids are processed one at a time.
- **Server time only:** client clocks are never trusted.
- **Ranking:** by each supplier's best total (freight + origin + destination); ties go to the earlier bid.
- A supplier's new bid must be lower than their own previous best.
- No authentication (supplier name is typed in), to keep scope simple. A production version would add login and roles.
- Status is computed on read instead of a background job, so there is nothing to keep in sync.