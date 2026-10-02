"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";
import '@/app/globals.css';

type MessageState = { text: string; isError: boolean };

export default function AccountSettings() {
  const router = useRouter();
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const [newUsername, setNewUsername] = useState("");
  const [confirmPassForUser, setConfirmPassForUser] = useState("");
  const [usernameMsg, setUsernameMsg] = useState<MessageState | null>(null);
  const [currentPass, setCurrentPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [passwordMsg, setPasswordMsg] = useState<MessageState | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deletePass, setDeletePass] = useState("");
  const [deleteMsg, setDeleteMsg] = useState<MessageState | null>(null);
  const [accountDeleted, setAccountDeleted] = useState(false);

  // ── Username ──────────────────────────────────────────────────────────────
  const handleUsernameChange = async () => {
    if (!newUsername.trim())
      return setUsernameMsg({ text: "Please enter a new username.", isError: true });
    if (!confirmPassForUser)
      return setUsernameMsg({ text: "Please enter your current password to confirm.", isError: true });

    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError || !user)
      return setUsernameMsg({ text: "Not authenticated.", isError: true });

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: user.email!,
      password: confirmPassForUser,
    });
    if (signInError)
      return setUsernameMsg({ text: "Incorrect password.", isError: true });

    const { error: updateError } = await supabase
      .from("profiles")
      .update({ username: newUsername.trim() })
      .eq("id", user.id);

    if (updateError) {
      setUsernameMsg({ text: "Failed to update username. Please try again.", isError: true });
    } else {
      setUsernameMsg({ text: "Username updated successfully.", isError: false });
      setNewUsername("");
      setConfirmPassForUser("");
    }
  };

  // ── Password ──────────────────────────────────────────────────────────────
  const handlePasswordChange = async () => {
    if (!currentPass || !newPass || !confirmPass)
      return setPasswordMsg({ text: "Please fill in all fields.", isError: true });
    if (newPass !== confirmPass)
      return setPasswordMsg({ text: "New passwords do not match.", isError: true });
    if (newPass.length < 8)
      return setPasswordMsg({ text: "Password must be at least 8 characters.", isError: true });

    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError || !user)
      return setPasswordMsg({ text: "Not authenticated.", isError: true });

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email: user.email!,
      password: currentPass,
    });
    if (signInError)
      return setPasswordMsg({ text: "Incorrect current password.", isError: true });

    // Supabase invalidates the current session after a password change —
    // sign out and redirect to /login so the user re-authenticates.
    const { error: updateError } = await supabase.auth.updateUser({ password: newPass });
    if (updateError) {
      setPasswordMsg({ text: "Failed to update password. Please try again.", isError: true });
    } else {
      setPasswordMsg({ text: "Password updated. Redirecting to login…", isError: false });
      await supabase.auth.signOut();
      setTimeout(() => router.push("/"), 1500);
    }
  };

  // ── Delete account ────────────────────────────────────────────────────────
  // Uses an API route because auth.admin.deleteUser() requires the
  // service role key, which must never be exposed to the browser.
  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE")
      return setDeleteMsg({ text: "Please type DELETE exactly to confirm.", isError: true });
    if (!deletePass)
      return setDeleteMsg({ text: "Please enter your password.", isError: true });

    const res = await fetch("/api/account/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ currentPassword: deletePass }),
    });
    const data = await res.json();

    if (!res.ok) {
      setDeleteMsg({ text: data.error ?? "Failed to delete account. Please try again.", isError: true });
    } else {
      setAccountDeleted(true);
      setDeleteMsg({ text: "Your account has been deleted.", isError: false });
    }
  };

  const StatusMessage = ({ msg }: { msg: MessageState | null }) => {
    if (!msg) return null;
    return (
      <p className={`gl-msg ${msg.isError ? "gl-msg--error" : "gl-msg--success"}`}>
        {msg.text}
      </p>
    );
  };

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto", padding: "1.5rem 1rem" }}>

      {/* Navbar */}
      <nav className="gl-nav">
        <h1 className="gl-nav__title">Greenlab Cell Detection</h1>
        <div className="gl-nav__links">
          <a href="/dashboard" className="gl-nav__link">Home</a>
        </div>
      </nav>

      {/* Change Password */}
      <div className="gl-card">
        <h2 className="gl-settings__section-title">Change password</h2>
        <label className="gl-settings__label">Current password</label>
        <input
          type="password"
          value={currentPass}
          onChange={e => setCurrentPass(e.target.value)}
          placeholder="Enter current password"
          className="gl-input"
        />
        <label className="gl-settings__label">New password</label>
        <input
          type="password"
          value={newPass}
          onChange={e => setNewPass(e.target.value)}
          placeholder="Enter new password"
          className="gl-input"
        />
        <label className="gl-settings__label">Confirm new password</label>
        <input
          type="password"
          value={confirmPass}
          onChange={e => setConfirmPass(e.target.value)}
          placeholder="Confirm new password"
          className="gl-input gl-input--last"
        />
        <button onClick={handlePasswordChange} className="gl-btn gl-btn--outline">
          Save password
        </button>
        <StatusMessage msg={passwordMsg} />
      </div>

      {/* Delete Account */}
      <div className="gl-card gl-card--danger">
        <h2 className="gl-settings__section-title gl-settings__section-title--danger">
          Delete account
        </h2>
        <p className="gl-settings__hint">
          This permanently removes your account and all associated data. This action cannot be undone.
        </p>
        {!accountDeleted && (
          <button
            onClick={() => setShowDeleteConfirm(v => !v)}
            className="gl-btn gl-btn--danger-outline"
          >
            Delete my account
          </button>
        )}
        {showDeleteConfirm && !accountDeleted && (
          <div className="gl-danger-confirm">
            <p className="gl-danger-confirm__title">Are you absolutely sure?</p>
            <p className="gl-danger-confirm__hint">
              Type <strong>DELETE</strong> below and enter your password to confirm.
            </p>
            <label className="gl-settings__label">Confirmation</label>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={e => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE"
              className="gl-input"
            />
            <label className="gl-settings__label">Current password</label>
            <input
              type="password"
              value={deletePass}
              onChange={e => setDeletePass(e.target.value)}
              placeholder="Enter your password"
              className="gl-input gl-input--last"
            />
            <div style={{ display: "flex", gap: "8px" }}>
              <button onClick={handleDeleteAccount} className="gl-btn gl-btn--danger-outline">
                Confirm delete
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText("");
                  setDeletePass("");
                  setDeleteMsg(null);
                }}
                className="gl-btn gl-btn--outline"
              >
                Cancel
              </button>
            </div>
            <StatusMessage msg={deleteMsg} />
          </div>
        )}
        {accountDeleted && (
          <p className="gl-msg gl-msg--error" style={{ marginTop: "8px" }}>
            Your account has been deleted.
          </p>
        )}
      </div>

      {/* Footer */}
      <footer className="gl-footer">
        <p className="gl-footer__body">
          Greenlab is a Tulane University research tool for automated AI cell detection and analysis
          using deep learning. Upload microscopy images to detect and count cells with precision.
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
          Please Note: Greenlab is still in development. Accurate results are not guaranteed
        </p>
      </footer>
    </div>
  );
}