import './globals.css'
import { Inter } from 'next/font/google'
import { colors } from '@/constants/colors'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'ReFind - PDF Reference Manager',
  description: 'A tool for managing and querying academic paper references',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" style={{ background: colors.background }}>
      <body className={inter.className} suppressHydrationWarning style={{ background: colors.background }}>
        <div style={{ background: colors.background, minHeight: '100vh' }}>
          <nav style={{ background: colors.background, boxShadow: `0 1px 2px ${colors.shadow}` }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <span style={{ color: colors.primary }} className="text-xl font-bold">ReFind</span>
                  </div>
                </div>
              </div>
            </div>
          </nav>
          <main style={{ background: colors.background }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
