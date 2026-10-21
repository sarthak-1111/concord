import './globals.css';
import React from 'react';

export const metadata = { title: 'Concord', description: 'XRD, PDF and XAFS of one sample, cross-checked' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f9f2e4]">{children}</body>
    </html>
  );
}
