'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import '@/app/globals.css';

export default function Home() {
  const router = useRouter();
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const [tab, setTab] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError('Invalid email or password.');
    } else {
      router.push('/dashboard');
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');

    if (!email.endsWith('@tulane.edu')) {
      return setError('Only @tulane.edu email addresses are allowed.');
    }

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { username: email.split('@')[0] },
      },
    });

    if (error) {
      setError(error.message);
    } else {
      setSuccess('Account created! Check your email to confirm, then log in.');
      setTab('login');
    }
  };

  return (
    <main className="gl-page gl-page--centered">
      <div className="gl-card gl-card--auth">
        <h1 className="gl-auth__title">Welcome to Greenlab</h1>
        <p className="gl-auth__subtitle">AI Cell Detection Platform</p>

        {/* Tab Switcher */}
        <div className="gl-tabs">
          {(['login', 'signup'] as const).map(t => (
            <button
              key={t}
              type="button"
              onClick={() => { setTab(t); setError(''); setSuccess(''); }}
              className={`gl-tab${tab === t ? ' gl-tab--active' : ''}`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={tab === 'login' ? handleLogin : handleSignup}>
          <input
            className="gl-input"
            placeholder={tab === 'signup' ? 'Tulane Email (@tulane.edu)' : 'Email'}
            type="email"
            name="email"
            autoComplete="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
          <input
            className="gl-input gl-input--last"
            placeholder="Password"
            type="password"
            name="password"
            autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
            value={password}
            onChange={e => setPassword(e.target.value)}
          />

          {error   && <p className="gl-msg gl-msg--error">{error}</p>}
          {success && <p className="gl-msg gl-msg--success">{success}</p>}

          <button type="submit" className="gl-btn gl-btn--primary gl-btn--full">
            {tab === 'login' ? 'Login' : 'Sign Up'}
          </button>
        </form>
      </div>

      {/* Footer */}
      <footer className="gl-footer">
        <p className="gl-footer__body">
          Greenlab is a Tulane University research tool for automated AI cell
          detection and analysis using deep learning. Upload microscopy images
          to detect and count cells with precision.
        </p>
        <p className="gl-footer__copy">© 2026 Greenlab · Tulane University 🌊</p>
        <a
          href="https://portfolio-site-wheat-delta.vercel.app"
          target="_blank"
          className="gl-footer__link"
        >
          Built by Mason Mitchell
        </a>
        <p className="gl-footer__disclaimer">
          Please Note: Greenlab is still in development. Accurate results are not guaranteed.
        </p>
      </footer>
    </main>
  );
}