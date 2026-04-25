import { useState } from 'react'
import { uploadPhoto } from '../api/memberApi'

const defaultForm = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  city: '',
  state: '',
  country: '',
  headline: '',
  about_summary: '',
  skills: '',
  profile_photo_url: '',
  resume_text: '',
}

function getInitials(firstName = '', lastName = '') {
  const first = firstName.trim().charAt(0)
  const last = lastName.trim().charAt(0)
  return `${first}${last}`.toUpperCase() || 'M'
}

export default function ProfileForm({
  initialValues = defaultForm,
  onSubmit,
  submitText = 'Save Profile',
  memberId = null,
}) {
  const [form, setForm] = useState({
    ...defaultForm,
    ...initialValues,
    skills: Array.isArray(initialValues.skills)
      ? initialValues.skills.join(', ')
      : initialValues.skills || '',
  })
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [uploading, setUploading] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handlePhotoUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadMessage('')
    setUploadError('')

    try {
      const data = await uploadPhoto(file, memberId)
      setForm((current) => ({
        ...current,
        profile_photo_url: data.profile_photo_url || '',
      }))
      setUploadMessage('Profile photo uploaded successfully.')
    } catch (error) {
      setUploadError(error.message)
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    onSubmit({
      ...form,
      skills: form.skills
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      experience: [],
      education: [],
    })
  }

  return (
    <form className="profile-form" onSubmit={handleSubmit}>
      <section className="card">
        <div className="section-heading">
          <h3>Basic information</h3>
          <p>Enter the member’s identity and headline details.</p>
        </div>

        <div className="form-grid two-column">
          <div className="field">
            <label htmlFor="first_name">First name</label>
            <input
              id="first_name"
              name="first_name"
              value={form.first_name}
              onChange={handleChange}
              placeholder="Nikhil"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="last_name">Last name</label>
            <input
              id="last_name"
              name="last_name"
              value={form.last_name}
              onChange={handleChange}
              placeholder="Kulkarni"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="name@example.com"
              type="email"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="phone">Phone</label>
            <input
              id="phone"
              name="phone"
              value={form.phone}
              onChange={handleChange}
              placeholder="+1 (555) 555-5555"
            />
          </div>

          <div className="field field-full">
            <label htmlFor="headline">Headline</label>
            <input
              id="headline"
              name="headline"
              value={form.headline}
              onChange={handleChange}
              placeholder="MSDA Student | Data Engineering | FastAPI"
            />
          </div>
        </div>
      </section>

      <section className="card">
        <div className="section-heading">
          <h3>Location</h3>
          <p>Add city, state, and country for search and profile display.</p>
        </div>

        <div className="form-grid three-column">
          <div className="field">
            <label htmlFor="city">City</label>
            <input
              id="city"
              name="city"
              value={form.city}
              onChange={handleChange}
              placeholder="San Jose"
            />
          </div>

          <div className="field">
            <label htmlFor="state">State</label>
            <input
              id="state"
              name="state"
              value={form.state}
              onChange={handleChange}
              placeholder="CA"
            />
          </div>

          <div className="field">
            <label htmlFor="country">Country</label>
            <input
              id="country"
              name="country"
              value={form.country}
              onChange={handleChange}
              placeholder="USA"
            />
          </div>
        </div>
      </section>

      <section className="card">
        <div className="section-heading">
          <h3>Profile media</h3>
          <p>Upload a profile image or use the current photo already attached.</p>
        </div>

        <div className="photo-upload-layout">
          <div className="profile-photo-panel">
            {form.profile_photo_url ? (
              <img
                className="profile-photo-large"
                src={form.profile_photo_url}
                alt="Profile preview"
              />
            ) : (
              <div className="profile-photo-fallback large">
                {getInitials(form.first_name, form.last_name)}
              </div>
            )}
          </div>

          <div className="upload-panel">
            <div className="field">
              <label htmlFor="photo_upload">Profile photo upload</label>
              <input
                id="photo_upload"
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
              />
            </div>

            {uploading && <p className="meta-text">Uploading photo...</p>}
            {uploadMessage && <p className="alert success-alert">{uploadMessage}</p>}
            {uploadError && <p className="alert error-alert">{uploadError}</p>}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="section-heading">
          <h3>Professional summary</h3>
          <p>Use a short bio, skills list, and resume summary.</p>
        </div>

        <div className="form-grid">
          <div className="field">
            <label htmlFor="skills">Skills</label>
            <input
              id="skills"
              name="skills"
              value={form.skills}
              onChange={handleChange}
              placeholder="Python, FastAPI, Kafka, React"
            />
          </div>

          <div className="field">
            <label htmlFor="about_summary">About</label>
            <textarea
              id="about_summary"
              name="about_summary"
              value={form.about_summary}
              onChange={handleChange}
              placeholder="Write a short member summary..."
              rows="5"
            />
          </div>

          <div className="field">
            <label htmlFor="resume_text">Resume text</label>
            <textarea
              id="resume_text"
              name="resume_text"
              value={form.resume_text}
              onChange={handleChange}
              placeholder="Paste resume details or highlights..."
              rows="6"
            />
          </div>
        </div>
      </section>

      <div className="form-actions">
        <button type="submit" className="primary-button">
          {submitText}
        </button>
      </div>
    </form>
  )
}