import Sidebar from './Sidebar'

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 min-h-full animate-fadein">
          {children}
        </div>
      </main>
    </div>
  )
}
