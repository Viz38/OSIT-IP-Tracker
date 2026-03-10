# Detective Pradeep 🕵️
**(Formerly OSIT-IP-Tracker)**

A modern, full-stack Next.js application to track the intelligence of companies by resolving their domain names. Includes a sleek UI to manage targets, fetch advanced intel, and export results to CSV.

## Features
- **Add Targets:** Easily input a company name and its domain manually.
- **Bulk Upload:** Upload targets simultaneously via CSV.
- **Fetch Intel:** Resolves domains to IP addresses, geolocates them, and checks HTTP status.
- **Supabase Powered:** Real-time data storage and management.
- **Vercel Ready:** Optimized for hosting on Vercel.

## Technology Stack
- **Framework:** Next.js 14+ (App Router)
- **Database:** Supabase (Postgres)
- **Styling:** Tailwind CSS + Custom Global CSS
- **Language:** TypeScript

## Installation

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Environment Variables:** Create a `.env.local` file with:
    ```
    NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
    NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
    SUPABASE_SERVICE_ROLE_KEY=your_service_role_key (for API updates)
    ```

## Running Locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Usage

1.  **Add Targets:** Enter details on the home page or upload a CSV.
2.  **Fetch Data:** On the "View Results" page, click **"🔄 Fetch Data"**.
3.  **Export:** Click **"⬇️ Export CSV"** to download your intel report.
