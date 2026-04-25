import { useState } from 'react'
import { Link } from 'react-router-dom'
import { searchMembers } from '../api/memberApi'

function getInitials(firstName = '', lastName = '') {
  const first = firstName.trim().charAt(0)
  const last = lastName.trim().charAt(0)
  return `${first}${last}`.toUpperCase() || 'M'
}

export default function HomePage() {
  const [filters, setFilters] = useState({ skill: '', location: '', keyword: '' })
  const [members, setMembers] = useState([])
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (event) => {
    const { name, value } = event.target
    setFilters((current) => ({ ...current, [name]: value }))
  }

  const handleSearch = async (event) => {
    event.preventDefault()
    setError('')
    setSearched(true)

    try {
      const data = await searchMembers(filters)
      setMembers(data.members || [])
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="home-dashboard">
      <div className="home-intro card">
        <div>
          <p className="home-label">Member directory</p>
          <h1>Find and manage member profiles</h1>
          <p>
            Search existing members, open profile pages, or create a new profile.
          </p>
        </div>

        <Link to="/members/create" className="btn primary">
          Create profile
        </Link>
      </div>

      <form className="home-search card" onSubmit={handleSearch}>
        <div className="home-search-top">
          <div>
            <h2>Quick search</h2>
            <p>Search by skill, location, or keyword.</p>
          </div>

          <button type="submit" className="btn primary">
            Search
          </button>
        </div>

        <div className="home-search-fields">
          <div className="field">
            <label htmlFor="home-skill">Skill</label>
            <input
              id="home-skill"
              name="skill"
              value={filters.skill}
              onChange={handleChange}
              placeholder="Python"
            />
          </div>

          <div className="field">
            <label htmlFor="home-location">Location</label>
            <input
              id="home-location"
              name="location"
              value={filters.location}
              onChange={handleChange}
              placeholder="San Jose"
            />
          </div>

          <div className="field">
            <label htmlFor="home-keyword">Keyword</label>
            <input
              id="home-keyword"
              name="keyword"
              value={filters.keyword}
              onChange={handleChange}
              placeholder="data engineering"
            />
          </div>
        </div>
      </form>

      {error && <p className="alert error">{error}</p>}

      <div className="home-results-heading">
        <h2>{searched ? 'Search results' : 'Profiles'}</h2>
        <Link to="/members/search">Advanced search</Link>
      </div>

      <div className="home-results-list">
        {members.length === 0 ? (
          <div className="card home-empty">
            <p>{searched ? 'No matching profiles found.' : 'Use quick search to find member profiles.'}</p>
          </div>
        ) : (
          members.slice(0, 5).map((member) => {
            const location = [member.city, member.state, member.country]
              .filter(Boolean)
              .join(', ')

            return (
              <article key={member.member_id} className="card home-result">
                {member.profile_photo_url ? (
                  <img
                    className="home-result-avatar"
                    src={member.profile_photo_url}
                    alt={`${member.first_name} ${member.last_name}`}
                  />
                ) : (
                  <div className="home-result-avatar fallback">
                    {getInitials(member.first_name, member.last_name)}
                  </div>
                )}

                <div className="home-result-main">
                  <h3>{member.first_name} {member.last_name}</h3>
                  <p>{member.headline || 'No headline provided'}</p>
                  <span>{location || 'Location not provided'}</span>
                </div>

                <Link to={`/members/${member.member_id}`} className="btn secondary small">
                  View
                </Link>
              </article>
            )
          })
        )}
      </div>
    </section>
  )
}
