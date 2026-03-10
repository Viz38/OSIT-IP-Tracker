# CHANGELOG
All notable changes to this project are documented here.

## [2026-03-10] Project Cleanup & Nest.js Finalization
- [Directory]: Removed all legacy Python files (`app.py`, `requirements.txt`, `ips.db`).
- [Directory]: Removed Flask-specific folders (`templates/`, `static/`, `api/`).
- [vercel.json]: Removed legacy Vercel Python configuration.
- Reason: Cleaned up the project structure to be a pure Next.js application as requested by the user.

## [2026-03-10] Migrate to Next.js & Supabase
- [src/app]: Rebuilt the entire application using Next.js 14 and React.
- [src/lib/supabase.ts]: Integrated Supabase client for cloud data management.
- [src/app/api/fetch]: Implemented domain resolution and geolocation in Node.js.
- [README.md]: Updated with Next.js installation and usage instructions.
- Reason: User requested transition to Next.js for better Vercel integration and modern stack.
