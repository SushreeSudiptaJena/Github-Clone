# Deploy frontend to Vercel (quick steps)

1. Create a Vercel account and import the GitHub repo.
2. When configuring the project, set the Root Directory to `frontend`.
3. Build Command: `npm run build`
4. Output Directory: `dist`
5. Add Environment Variable in Vercel project settings:
   - `VITE_API_URL` = `https://your-backend-url` (set to your Render backend URL)
6. Deploy — Vercel will provide a public URL for the frontend.

Local testing:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
