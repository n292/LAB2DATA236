import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ProfileForm from '../components/ProfileForm'
import { getMember, updateMember } from '../api/memberApi'

export default function EditProfilePage() {
  const { memberId } = useParams()
  const navigate = useNavigate()
  const [member, setMember] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const loadMember = async () => {
      try {
        const data = await getMember(memberId)
        setMember(data.member)
      } catch (err) {
        setError(err.message)
      }
    }

    loadMember()
  }, [memberId])

  const handleSubmit = async (payload) => {
    setMessage('')
    setError('')

    try {
      await updateMember({ member_id: memberId, ...payload })
      setMessage('Member updated successfully.')
      setTimeout(() => navigate(`/members/${memberId}`), 700)
    } catch (err) {
      setError(err.message)
    }
  }

  if (error) {
    return <p className="alert error-alert">{error}</p>
  }

  if (!member) {
    return <p className="card loading-card">Loading member profile...</p>
  }

  return (
    <section className="page-stack">
      <div className="card page-banner">
        <p className="eyebrow">Profile management</p>
        <h1 className="page-title">Edit Member Profile</h1>
        <p className="page-description">
          Update the selected member’s details and save the revised profile.
        </p>
      </div>

      {message && <p className="alert success-alert">{message}</p>}
      {error && <p className="alert error-alert">{error}</p>}

      <ProfileForm
        initialValues={member}
        onSubmit={handleSubmit}
        submitText="Save changes"
        memberId={memberId}
      />
    </section>
  )
}