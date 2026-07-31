# JoshReadingOnline — Personal Ebook Reader

A single-user ebook reader web app for PDFs and EPUBs stored in Google Drive. Features a library view like Calibre and reading views powered by pdf.js and epubjs, with reading progress synced back to Drive via appProperties.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Auth**: NextAuth v4 with Google OAuth
- **Rendering**: pdfjs-dist (PDF), epubjs (EPUB)
- **Deployment**: Vercel (server features required)

## Google Cloud Setup

This copy is intended for the personal Google Drive account `joshualparris@gmail.com`.
For a personal Gmail account, create a Google Cloud OAuth app with an **External** consent screen and add `joshualparris@gmail.com` as a test user while the app is unpublished.

### 1. Confirm the GCP project

- Project ID: your personal Google Cloud project
- Google Drive API: enabled
- OAuth consent screen: **External**
- Test user: `joshualparris@gmail.com`
- Authorized redirect URI (dev): `http://localhost:3000/api/auth/callback/google`

### 2. Enable the Google Drive API

1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for **Google Drive API**
3. Click on it and press **ENABLE**

### 3. Configure OAuth Consent Screen

1. In the left sidebar, go to **APIs & Services** → **OAuth consent screen**
2. Confirm the app type is **External**
3. Confirm the app has the scope:
   - `https://www.googleapis.com/auth/drive`
4. Add `joshualparris@gmail.com` as a test user

### 4. Create or verify OAuth Credentials

1. In the left sidebar, go to **APIs & Services** → **Credentials**
2. Ensure the OAuth Client ID exists for the internal app
3. If needed, create **OAuth client ID** → **Web application**
4. Add authorized redirect URI:
   - `http://localhost:3000/api/auth/callback/google`
5. Save the **Client ID** and **Client Secret** securely

### 5. Personal Gmail notes

- Unpublished External apps are limited to test users
- Google may show an unverified app screen during local development
- Refresh tokens for testing-mode external apps can expire, so you may need to sign in again occasionally

### Troubleshooting

If sign-in fails, check that `joshualparris@gmail.com` is listed as a test user on the OAuth consent screen and that the redirect URI exactly matches `NEXTAUTH_URL` plus `/api/auth/callback/google`.

## Local Setup

## Local Setup

### 1. Set Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and fill in:

```
GOOGLE_CLIENT_ID=<your_client_id_from_step_4>
GOOGLE_CLIENT_SECRET=<your_client_secret_from_step_4>
NEXT_PUBLIC_GOOGLE_API_KEY=<your_google_api_key>
NEXTAUTH_SECRET=<generate_a_random_string>
NEXTAUTH_URL=http://localhost:3000
ALLOWED_GOOGLE_EMAIL=joshualparris@gmail.com
```

To generate `NEXTAUTH_SECRET`, run:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Run Dev Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and click **Sign in with Google**.

### 4. Add Drive Folder IDs

Create or choose folders in the `joshualparris@gmail.com` Google Drive, then paste their folder IDs into `.env.local`:

```
GOOGLE_DRIVE_FOLDER_IT_PD_EBOOKS=
GOOGLE_DRIVE_FOLDER_BOOK_CLUB=
GOOGLE_DRIVE_FOLDER_UNSORTED=
GOOGLE_DRIVE_FOLDER_AVANCE_KBS=
GOOGLE_DRIVE_FOLDER_ITIL_PDFS=
GOOGLE_DRIVE_FOLDER_ITIL=
GOOGLE_DRIVE_FOLDER_ITIL_PRINCE_COBIT=
GOOGLE_DRIVE_FOLDER_IEC_27001=

# Optional audiobook matching/link folders
GOOGLE_DRIVE_AUDIOBOOK_FOLDER_OUTLANDER=
GOOGLE_DRIVE_AUDIOBOOK_FOLDER_OTHER=
NEXT_PUBLIC_GOOGLE_DRIVE_AUDIOBOOK_FOLDER_OUTLANDER=
NEXT_PUBLIC_GOOGLE_DRIVE_AUDIOBOOK_FOLDER_OTHER=
```

The folder ID is the final part of a Drive folder URL, for example `https://drive.google.com/drive/folders/<folder_id>`.

## Project Structure

```
app/
  api/
    auth/[...nextauth]/    # NextAuth routes
    library/               # GET /api/library (list books)
    library/progress/      # POST /api/library/progress (save progress)
  page.tsx                 # Sign-in landing page
  layout.tsx               # Root layout with AuthProvider
  providers.tsx            # Client SessionProvider wrapper
lib/
  googleDrive.ts          # Drive helper functions
types/
  books.ts                # Shared BookEntry types
middleware.ts             # Protect /library and /reader routes
```

## Acceptance Criteria — Phase 1

✅ `npm run build` passes with no TypeScript errors
✅ Sign in with Google works
✅ GET `/api/library` returns real files from Drive folders
✅ POST `/api/library/progress` writes appProperties visible in Drive

## Next Phase

Phase 2 (PowerShell sync script) will upload local books from `C:\dev\Books` to the "Local Books" folder in Drive.
