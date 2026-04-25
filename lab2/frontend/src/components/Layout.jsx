import { NavLink } from 'react-router-dom'

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/members/search" className="brand">
            <span className="brand-box">in</span>
            <span className="brand-text">Profiles</span>
          </NavLink>

          <nav className="nav">
            <NavLink
              to="/members/search"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Search
            </NavLink>

            <NavLink
              to="/members/create"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Create
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="page">
        {children}
      </main>
    </div>
  )
}