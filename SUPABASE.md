# Using Supabase as the database (quick guide)

This file shows how to create a free Supabase Postgres DB and get the connection string to use with this project.

## 1) Create a Supabase project
1. Go to https://app.supabase.com and sign up.  
2. Create a new project → give it a name and password (the password is your DB user password).  
3. Wait for the project to finish provisioning.

## 2) Get the connection string
1. Open your Supabase project → Settings → Database → Connection string.  
2. Copy the **Connection string (URI)**. It looks like:

   postgres://postgres:password@db.123xyz.supabase.co:5432/postgres

3. For async SQLAlchemy (this repo uses asyncpg), transform it by adding the async driver prefix:

   postgresql+asyncpg://postgres:password@db.123xyz.supabase.co:5432/postgres

4. Use that as your `DATABASE_URL` (see `GITHUB_SECRETS.md` for where to store it).

## 3) Allow network / row-level policy notes
- Supabase has row-level security (RLS) on by default for some tables — this project uses its own DB migrations and API, so you don't need to enable Supabase Auth to use the DB.  
- If you use Supabase Auth later, consult Supabase docs to configure policies.

## 4) Run migrations against Supabase
- Locally (after you set `DATABASE_URL` in your shell):
  ```bash
  export DATABASE_URL='postgresql+asyncpg://postgres:password@db.123xyz.supabase.co:5432/postgres'
  cd backend
  alembic upgrade head
  ```
- Using GitHub Actions: add `DATABASE_URL` as a repository secret (see `GITHUB_SECRETS.md`) so `.github/workflows/migrate.yml` can run migrations automatically.

## 5) Troubleshooting
- Connection refused / cannot connect: check that your DB is healthy in Supabase dashboard and that password is correct.  
- If you see SSL errors, the Supabase connection string includes SSL by default; SQLAlchemy/asyncpg should handle it.

---
If you'd like, I can add a small script `scripts/supabase_init.sh` that checks the connection and runs `alembic upgrade head` automatically — should I add it? (Yes/No)
