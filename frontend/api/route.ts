// app/api/account/delete/route.ts
import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";
import { createClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";

// Admin client — uses the service role key, never exposed to the browser.
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

export async function POST(req: NextRequest) {
  const { currentPassword } = await req.json();

  if (!currentPassword)
    return NextResponse.json({ error: "Password is required." }, { status: 400 });

  const cookieStore = await cookies();

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        },
      },
    }
  );

  // 1. Verify the session exists
  const { data: { user }, error: userError } = await supabase.auth.getUser();
  if (userError || !user)
    return NextResponse.json({ error: "Not authenticated." }, { status: 401 });

  // 2. Re-authenticate to confirm identity before destructive action
  const { error: signInError } = await supabase.auth.signInWithPassword({
    email: user.email!,
    password: currentPassword,
  });
  if (signInError)
    return NextResponse.json({ error: "Incorrect password." }, { status: 403 });

  // 3. Delete the profile row (admin client bypasses RLS)
  await supabaseAdmin.from("profiles").delete().eq("id", user.id);

  // 4. Delete the auth user — irreversible
  const { error: deleteError } = await supabaseAdmin.auth.admin.deleteUser(user.id);
  if (deleteError)
    return NextResponse.json({ error: "Failed to delete account." }, { status: 500 });

  // 5. Sign the user out
  await supabase.auth.signOut();

  return NextResponse.json({ message: "Account deleted successfully." });
}