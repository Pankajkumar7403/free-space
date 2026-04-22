import { type NextRequest, NextResponse } from 'next/server';

const API_INTERNAL = process.env.API_INTERNAL_URL ?? 'http://127.0.0.1:8000/api/v1';

export async function GET(request: NextRequest): Promise<NextResponse> {
  const provider = request.nextUrl.searchParams.get('provider');
  const redirectUri = request.nextUrl.searchParams.get('redirect_uri');

  if (!provider || !redirectUri) {
    return NextResponse.json(
      { error: 'provider and redirect_uri are required' },
      { status: 400 },
    );
  }

  try {
    const res = await fetch(
      `${API_INTERNAL}/users/oauth/${encodeURIComponent(provider)}/init/?redirect_uri=${encodeURIComponent(redirectUri)}`,
      { method: 'GET', cache: 'no-store' },
    );

    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return NextResponse.json({ error: 'oauth init request failed' }, { status: 502 });
  }
}
