import { useState } from 'react'
import ProfileForm from '../components/ProfileForm'
import { createMember } from '../api/memberApi'

export default function CreateProfilePage() {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (payload) => {
    setMessage('')
    setError('')

    try {
      const data = await createMember(payload)
      setMessage(`${data.message} (${data.member_id})`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page-stack">
      <div className="card page-banner">
        <p className="eyebrow">Profile management</p>
        <h1 className="page-title">Create Member Profile</h1>
        <p className="page-description">
          Create a new member profile with contact information, location, skills,
          about summary, resume text, and photo.
        </p>
      </div>

      {message && <p className="alert success-alert">{message}</p>}
      {error && <p className="alert error-alert">{error}</p>}

      <ProfileForm onSubmit={handleSubmit} submitText="Create profile" />
    </section>
  )
}