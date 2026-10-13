# NutriFit — Frontend UI update

## Scope

This package contains the updated `frontend/` directory only. It is based on the uploaded `feature/nutrition-mysql-food-catalog` frontend because that branch contains the newer Nutrition V4 / Food Catalog interface. Backend business logic and database schema were intentionally not changed in this package.

## What changed

- Preserved the existing NutriFit page layout and profile / meal planner UI.
- Added the floating NutriFit AI Chatbox UI, streaming response reader, and per-tab `sessionStorage` conversation history.
- Added a Premium Quick Food dialog with the required flow: search -> explicitly select a result -> request Backend preview -> confirm that the meal was actually consumed -> confirm through Backend. The browser does not calculate calories/macros itself.
- Replaced the Street Food placeholder with a real catalog/filter/recommendation interface connected to the TV4 API contract.
- Restored the Workout section that was previously hidden and connected its API adapter to the TV4 workout/progress contract.
- Updated the API client to map TV4 snake_case responses to existing UI field names and to use `credentials: "include"` for authenticated Nutrition / Workout requests.
- Added a configurable API base. By default it targets `http://127.0.0.1:5000`; set `window.NUTRIFIT_API_BASE_URL` before the Frontend scripts if using another server.
- Set the floating Chatbox below modal dialogs so it does not cover Quick Food or other dialogs.

## Files added

- `frontend/assets/css/chatbox.css`
- `frontend/assets/css/quick-food.css`
- `frontend/assets/css/street-food.css`
- `frontend/js/chatbox.js`
- `frontend/js/quick-food.js`
- `frontend/js/street-food.js`

## Files updated

- `frontend/index.html`
- `frontend/js/api.js`
- `frontend/js/app.js`
- `frontend/js/workouts.js`

Other existing Frontend files are included as part of the complete `frontend/` folder so you can replace the folder as a unit if needed.

## Backend contracts required after the team's branches are integrated

This package does not include or modify Backend files. The final integrated backend must provide:

- Nutrition V4 / Food Intake / Food Catalog endpoints from the TV3 branch.
- Quick Food API endpoints documented in `docs/PREMIUM_QUICK_FOOD_API.md`:
  - `GET /api/nutrition/quick-food/search`
  - `POST /api/nutrition/quick-food/preview`
  - `POST /api/nutrition/quick-food/confirm`
- TV4 Workout / Progress endpoints:
  - `/api/workouts/catalog`, `/api/workouts/categories`, `/api/workouts/custom`, `/api/workouts/logs`, `/api/workouts/log`
  - `/api/progress/weekly/<user_id>`
- TV4 Street Food endpoints:
  - `GET /api/street-food`
  - `POST /api/street-food/recommend`
- Chatbox Backend endpoint from `feature/chatbox-ai`:
  - `POST /api/chatbot/chat` (streaming SSE supported; ordinary JSON response is also supported)

The Frontend will show a clear error when an endpoint is missing rather than inventing catalog data. Quick Food is Premium-only. The backend contract notes that a missing Premium schema may return `PREMIUM_UNAVAILABLE`; the UI surfaces this state and does not bypass it.

## Local run

1. Integrate/register the required backend blueprints on the team's backend branch; keep the existing `.env` local and do not include it in Git.
2. Start the Flask backend on port 5000.
3. Open `frontend/index.html` with VS Code Live Server (commonly `http://127.0.0.1:5500/frontend/index.html`) rather than opening it as a `file://` URL.
4. Sign in through the existing UI. Authenticated API requests rely on the login cookie and `credentials: "include"`.
5. Configure Gemini only in the Backend `.env`; never expose a Gemini key in Frontend code.

For deployment, set the API base to the deployed backend origin and configure CORS/cookies appropriately. The Chatbox endpoint may require the backend's CORS configuration to permit the deployed frontend origin.

## Validation performed

- `node --check` passed for all JavaScript files in this `frontend/js/` folder.
- Parsed the HTML to check that local scripts/styles referenced by `index.html` exist.
- Checked that HTML IDs are unique and inline event-handler names map to JavaScript functions.
- Static check confirms Street Food and Workout sections are no longer wrapped in `hidden inert` placeholders.

A live end-to-end Browser/API test was not completed in this environment. The Frontend still needs end-to-end testing against the team's integrated Flask backend and local MySQL data.
