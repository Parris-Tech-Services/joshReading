import { NextResponse } from 'next/server';

function hasRealGoogleClientId() {
  const clientId = process.env.GOOGLE_CLIENT_ID ?? '';
  return /^[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com$/.test(clientId);
}

export function GET() {
  return NextResponse.json({
    googleSignInConfigured: hasRealGoogleClientId() && Boolean(process.env.GOOGLE_CLIENT_SECRET),
  });
}
