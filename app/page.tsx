'use client';

import { signIn } from 'next-auth/react';
import { useEffect, useState } from 'react';

export default function Home() {
  const [googleConfigured, setGoogleConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    fetch('/api/config')
      .then((response) => response.json())
      .then((config: { googleSignInConfigured: boolean }) => {
        setGoogleConfigured(config.googleSignInConfigured);
      })
      .catch(() => setGoogleConfigured(false));
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-4">JoshReadingOnline</h1>
        <p className="text-xl text-slate-300 mb-12">
          Your personal ebook reader for Drive and rescued local books
        </p>
        <a
          href="/library"
          className="mr-3 inline-flex px-8 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition-colors"
        >
          Open local library
        </a>
        <button
          disabled={!googleConfigured}
          onClick={() => signIn('google', { callbackUrl: '/library' })}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          Sign in with Google
        </button>
        {googleConfigured === false ? (
          <p className="mx-auto mt-6 max-w-xl text-sm text-amber-200">
            Google sign-in needs a real OAuth client ID and secret in .env.local for
            joshualparris@gmail.com.
          </p>
        ) : null}
      </div>
    </div>
  );
}
