import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Detective Pradeep",
    description: "Track domain intel with style",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <nav className="navbar">
                    <div className="nav-container">
                        <Link href="/" className="nav-brand">🕵️ Detective Pradeep</Link>
                        <div className="nav-links">
                            <Link href="/" className="nav-item">Add Targets</Link>
                            <Link href="/results" className="nav-item">View Results</Link>
                        </div>
                    </div>
                </nav>
                <main className="container-custom">
                    {children}
                </main>
            </body>
        </html>
    );
}
