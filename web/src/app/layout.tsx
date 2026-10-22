import './globals.css';
import React from 'react';
import { Newsreader } from 'next/font/google';

export const metadata = { title: 'Concord', description: 'XRD, PDF and XAFS of one sample, cross-checked' };
export const viewport = { themeColor: [{ media: '(prefers-color-scheme: light)', color: '#f5f4ed' }, { media: '(prefers-color-scheme: dark)', color: '#141413' }] };

const serif = Newsreader({ subsets: ['latin'], variable: '--font-serif', display: 'swap' });
// before first paint, so a saved theme does not flash the other one
const THEME = `try{var t=localStorage.getItem('concord.theme');if(t)document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={serif.variable} suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: THEME }} /></head>
      <body>{children}</body>
    </html>
  );
}
