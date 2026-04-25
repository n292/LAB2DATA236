import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteMember, getMember } from '../api/memberApi'

function getInitials(firstName = '', lastName = '') {
  const first = firstName.trim().charAt(0)
  const last = lastName.trim().charAt(0)
  return `${first}${last}`.toUpperCase() || 'M'
}

export default function MemberDetailPage() {
  const { memberId } = useParams()
  const navigate = useNavigate()
  const [member, setMember] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadMember = async () => {
      try {
        const viewerId = localStorage.getItem('viewer_id') || null
        const data = await getMember(memberId, {
          viewerId,
          emitProfileViewed: true,
          viewSource: 'profile_page',
        })
        setMember(data.member)
      } catch (err) {
        setError(err.message)
      }
    }

    loadMember()
  }, [memberId])

  const handleDelete = async () => {
    if (!window.confirm('Delete this profile?')) return

    try {
      await deleteMember(memberId)
      navigate('/members/search')
    } catch (err) {
      setError(err.message)
    }
  }

  if (error) return <p className="alert error">{error}</p>
  if (!member) return <p className="card loading">Loading profile...</p>

  const location = [member.city, member.state, member.country].filter(Boolean).join(', ')

  return (
    <section className="profile-page compact-page">
      <div className="card profile-card">
        <div className="profile-header-simple">
          {member.profile_photo_url ? (
            <img
              className="profile-avatar-simple"
              src={member.profile_photo_url}
              alt={`${member.first_name} ${member.last_name}`}
            />
          ) : (
            <div className="profile-avatar-simple fallback">
              {getInitials(member.first_name, member.last_name)}
            </div>
          )}

          <div className="profile-main-simple">
            <h1>{member.first_name} {member.last_name}</h1>
            <p className="profile-subtle">{member.headline || 'No headline provided'}</p>
            <p className="profile-subtle">{location || 'Location not provided'}</p>
            <p className="profile-subtle">
              {member.email}{member.phone ? ` · ${member.phone}` : ''}
            </p>

            <div className="actions">
              <Link className="btn primary" to={`/members/${member.member_id}/edit`}>
                Edit
              </Link>
              <button className="btn danger" onClick={handleDelete}>
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      <section className="card section-card">
        <h2>About</h2>
        <p>{member.about_summary || 'No about summary added.'}</p>
      </section>

      <section className="card section-card">
        <h2>Skills</h2>
        {(member.skills || []).length > 0 ? (
          <div className="chips">
            {member.skills.map((skill) => (
              <span className="chip" key={skill}>{skill}</span>
            ))}
          </div>
        ) : (
          <p className="muted no-margin">No skills listed.</p>
        )}
      </section>

      <section className="card section-card">
        <h2>Resume</h2>
        <p className="prewrap">{member.resume_text || 'No resume text provided.'}</p>
      </section>
    </section>
  )
}