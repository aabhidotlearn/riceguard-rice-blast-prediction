# RiceGuard — rice blast screening portfolio

RiceGuard is an interview-ready full-stack portfolio project for rice leaf screening. It pairs a responsive React dashboard with a Django REST API, session authentication, image upload, a prediction history, and a user dashboard.

> **Model scope:** the bundled MLP is a reproducible portfolio model trained on the four disease classes in the attributed sample dataset. It has no healthy-leaf class and has not been validated on independent field photos. Results are candidate class matches for human review, not diagnosis or agronomic advice. If the model artifact is missing, the app falls back to a clearly labeled visual heuristic.

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
| GET | `/dashboard/` | Per-user scan counts and five most recent scans |
| GET | `/health/` | Service status |

The prediction response includes `disease`, `confidence`, `demo_mode`, `image_url`, and `created_at`. A `demo_mode: true` response explicitly identifies heuristic output.

## Run the sample classifier and minority-sampling workflow

The repository includes four labeled sample images and a small MLP artifact. In the app, sign in, choose **Blast**, **Blight**, **Brown spot**, or **Tungro** under “Run a labeled sample,” then run leaf screening. The app stores each sample scan in the signed-in user's history.

To retrain, download the [Rice Leaf Disease Image Samples dataset](https://data.mendeley.com/datasets/fwcj7stb8r/1), extract it so each class has its own folder, then run from `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ml/train_model.py "/path/to/Rice Leaf Disease Images"
```

The trainer extracts deterministic color and HSV-histogram features, holds out filename families before training, scales features, and applies SMOTE **only to the training split**. It reports class counts before and after SMOTE, holdout accuracy, macro F1, per-class metrics, and a confusion matrix. For a quick controlled minority-class demonstration, reduce Blast to 120 examples from a 400-per-class sample and save to a separate artifact:

```bash
python ml/train_model.py "/path/to/Rice Leaf Disease Images" --max-per-class 400 --minority-class Blast --minority-count 120 --output /tmp/riceguard-minority-demo.joblib
```

The default full-dataset run saves `predictions/artifacts/rice_disease_mlp.joblib` plus a metadata sidecar; set `RICE_BLAST_MODEL` to override the model path. Dependency versions for loading the bundled joblib artifact are pinned in `requirements.txt`; retrain after changing them.

The source dataset is mildly imbalanced and contains four disease classes but no healthy class. The reported holdout is internal to that dataset and does not prove generalization to field images. [SAMPLE_RUN.md](backend/ml/SAMPLE_RUN.md) records an executed run where Blast was intentionally reduced to a minority class before train-only SMOTE. See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md) for license and sample-image credits. For persistence format/version details, see the [scikit-learn model persistence guide](https://scikit-learn.org/stable/model_persistence.html).

For an image-based CNN, replace the feature extractor and match its training preprocessing exactly. Validate on an independent, representative field dataset before making performance claims.

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
