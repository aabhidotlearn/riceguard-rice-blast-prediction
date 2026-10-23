# RiceGuard — rice blast screening portfolio

RiceGuard is an interview-ready full-stack portfolio project for rice leaf screening. It pairs a responsive React dashboard with a Django REST API, session authentication, image upload, a prediction history, and a user dashboard.

> **Inference status:** the upload-to-result flow works locally, but the included no-weights mode is a transparent color heuristic for demonstrating the product flow. It is not a validated rice blast model and must not be used for crop decisions. The resume mentions an MLP project, but model weights and the training preprocessing were not part of the supplied files. Connect compatible validated weights with `RICE_BLAST_MODEL` before presenting predictions as model results.

## Stack

- **Frontend:** React 18 + Vite, custom responsive CSS
- **Backend:** Django 5 + Django REST Framework
- **Database:** SQLite locally; PostgreSQL by setting `DATABASE_URL`
- **Authentication:** Django session authentication, CSRF protection, registration/login/logout
- **Images:** Django media storage locally; use persistent object storage for production
- **Deployment:** Render or Railway for the API, Vercel for the frontend

## Run locally

### API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser # optional
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env             # optional; default is http://localhost:8000/api
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`). Create an account to save scans. Without an account the dashboard shows example rows and the upload prompts for sign-in.

## API

All routes are under `/api/`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/csrf/` | Set CSRF cookie for browser session |
| POST | `/auth/register/` | Register with `username`, `email`, `password` |
| POST | `/auth/login/` | Start authenticated session |
| POST | `/auth/logout/` | End session |
| GET | `/auth/me/` | Current account |
| GET, POST | `/predictions/` | List own history; multipart upload field `image` to screen |
| GET | `/dashboard/` | Counts and five most recent scans |
| GET | `/health/` | Service status |

The prediction response includes `disease`, `confidence`, `demo_mode`, `image_url`, and `created_at`. A `demo_mode: true` response explicitly identifies heuristic output.

## Connecting a trained model

`backend/predictions/inference.py` is the model boundary. The current feature extractor emits RGB channel means and brown/yellow pixel fractions. To use a trained classifier, align preprocessing and feature shape with training, install its runtime (for example `joblib` and scikit-learn), set `RICE_BLAST_MODEL` to the serialized pipeline path, and validate it on a held-out dataset. Do not use the example heuristic as a diagnostic.

For an image-based CNN, replace `extract_features`/`predict` with the exact resize, normalization, and tensor path used in training. Store model weights in persistent storage or package them as a deployment artifact; do not commit large or private weights by default.

## Deploy

### Render / Railway API

Deploy the `backend` directory as a Python web service. Build/install command: `pip install -r requirements.txt`. The included Render Blueprint runs migrations before Gunicorn starts; if using a paid Render plan with pre-deploy commands enabled, move `python manage.py migrate` to that field and use `gunicorn config.wsgi:application` as the start command. Set `DEBUG=false`, a strong `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS` to the API hostname, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to the exact Vercel origin, plus `DATABASE_URL` for PostgreSQL. Configure persistent media storage before accepting production uploads; ephemeral container disks do not preserve images across redeploys.

### Vercel frontend

Import the `frontend` directory as the project root, use `npm run build` and output `dist`, and set `VITE_API_URL=https://YOUR-API-HOST/api`. Since auth uses Django cookies, serve both apps over HTTPS and configure the API's CORS and CSRF origin values to match the deployed frontend origin. For a production cross-site cookie setup, set `SESSION_COOKIE_SECURE=true`, `CSRF_COOKIE_SECURE=true`, `SESSION_COOKIE_SAMESITE=None`, and `CSRF_COOKIE_SAMESITE=None` on the API service, and verify the hosting providers' cookie behavior.

## Security and production notes

- Replace the development secret key and set `DEBUG=false` in production.
- Set exact allowed hosts and frontend origins; do not use wildcards with credentialed CORS.
- Add rate limits and a registration abuse control before public launch.
- Configure object storage, image retention/deletion policy, monitoring, and backups.
- The result is decision support only. Confirm suspected disease with local agricultural expertise.
