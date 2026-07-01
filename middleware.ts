import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // ONLY check cookies here. localStorage is not available in middleware.
  const accessToken = request.cookies.get('access_token');
  
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') || 
                     request.nextUrl.pathname.startsWith('/register');
  const isProtectedPage = request.nextUrl.pathname.startsWith('/user-dashboard');

  // If no cookie and trying to access protected page, redirect to login
  if (!accessToken && isProtectedPage) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // If has cookie and trying to access auth page, redirect to dashboard
  if (accessToken && isAuthPage) {
    return NextResponse.redirect(new URL('/user-dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/user-dashboard/:path*', '/login', '/register']
};