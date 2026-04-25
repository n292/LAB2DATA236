const BASE_URL = 'http://localhost:8000/api/members'

async function parseResponse(response) {
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data?.error || data?.message || 'Request failed')
  }
  if (data.success === false) {
    throw new Error(data.error || data.message || 'Request failed')
  }
  return data
}

export async function createMember(payload) {
  const response = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseResponse(response)
}

export async function getMember(memberId, options = {}) {
  const {
    viewerId = null,
    emitProfileViewed = false,
    viewSource = null,
  } = options

  const response = await fetch(`${BASE_URL}/get`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      member_id: memberId,
      viewer_id: viewerId,
      emit_profile_viewed: emitProfileViewed,
      view_source: viewSource,
    }),
  })
  return parseResponse(response)
}

export async function updateMember(payload) {
  const response = await fetch(`${BASE_URL}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseResponse(response)
}

export async function deleteMember(memberId) {
  const response = await fetch(`${BASE_URL}/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ member_id: memberId }),
  })
  return parseResponse(response)
}

export async function searchMembers(payload) {
  const response = await fetch(`${BASE_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseResponse(response)
}

export async function uploadPhoto(file, memberId = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (memberId) {
    formData.append('member_id', memberId)
  }
  const response = await fetch(`${BASE_URL}/upload-photo`, {
    method: 'POST',
    body: formData,
  })
  return parseResponse(response)
}