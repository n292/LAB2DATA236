import { useState } from 'react'
import { Link } from 'react-router-dom'
import { searchMembers } from '../api/memberApi'

function getInitials(firstName = '', lastName = '') {
  const first = firstName.trim().charAt(0)
  const last = lastName.trim().charAt(0)
  return `${first}${last}`.toUpperCase() || 'M'
}

export default function SearchMembersPage() {
  const [filters, setFilters] = useState({ skill: '', location: '', keyword: '' })
  const [members, setMembers] = useState([])
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

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
    <section className="search-page compact-page">
      <form className="card search-card" onSubmit={handleSearch}>
        <div className="search-header">
          <div>
            <h1>Search members</h1>
            <p>Use skill, location, or keyword.</p>
          </div>

          <button type="submit" className="btn primary">
            Search
          </button>
        </div>

        <div className="search-fields">
          <div className="field">
            <label htmlFor="skill">Skill</label>
            <input
              id="skill"
              name="skill"
              value={filters.skill}
              onChange={handleChange}
              placeholder="Python"
            />
          </div>

          <div className="field">
            <label htmlFor="location">Location</label>
            <input
              id="location"
              name="location"
              value={filters.location}
              onChange={handleChange}
              placeholder="San Jose"
            />
          </div>

          <div className="field">
            <label htmlFor="keyword">Keyword</label>
            <input
              id="keyword"
              name="keyword"
              value={filters.keyword}
              onChange={handleChange}
              placeholder="data engineering"
            />
          </div>
        </div>
      </form>

      {error && <p className="alert error">{error}</p>}

      <div className="results-title-row">
        <h2>Results</h2>
        <span>{members.length} found</span>
      </div>

      <div className="results-list">
        {members.length === 0 ? (
          <div className="card empty-results">
            <p>{searched ? 'No matching members found.' : 'Run a search to see results.'}</p>
          </div>
        ) : (
          members.map((member) => {
            const location = [member.city, member.state, member.country]
              .filter(Boolean)
              .join(', ')

            return (
              <article key={member.member_id} className="card result-card">
                {member.profile_photo_url ? (
                  <img
                    className="result-avatar"
                    src={member.profile_photo_url}
                    alt={`${member.first_name} ${member.last_name}`}
                  />
                ) : (
                  <div className="result-avatar fallback">
                    {getInitials(member.first_name, member.last_name)}
                  </div>
                )}

                <div className="result-main">
                  <h3>{member.first_name} {member.last_name}</h3>
                  <p className="result-headline">{member.headline || 'No headline provided'}</p>
                  <p className="muted">{location || 'Location not provided'}</p>

                  {(member.skills || []).length > 0 && (
                    <div className="chips">
                      {(member.skills || []).slice(0, 5).map((skill) => (
                        <span className="chip" key={`${member.member_id}-${skill}`}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
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