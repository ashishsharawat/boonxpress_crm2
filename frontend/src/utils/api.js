/**
 * Call a Frappe whitelisted method.
 */
export async function call(method, args = {}) {
  const response = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body: JSON.stringify(args),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.exc || error.message || `API call failed: ${response.status}`)
  }

  const data = await response.json()
  return data.message
}

/**
 * Get a list of documents.
 */
export async function getList(doctype, { fields, filters, orderBy, pageLength, start } = {}) {
  const params = new URLSearchParams()
  if (fields) params.set('fields', JSON.stringify(fields))
  if (filters) params.set('filters', JSON.stringify(filters))
  if (orderBy) params.set('order_by', orderBy)
  if (pageLength) params.set('limit_page_length', pageLength)
  if (start) params.set('limit_start', start)

  const response = await fetch(`/api/resource/${doctype}?${params.toString()}`, {
    headers: {
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get ${doctype} list: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

/**
 * Get a single document.
 */
export async function getDoc(doctype, name) {
  const response = await fetch(`/api/resource/${doctype}/${name}`, {
    headers: {
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get ${doctype}/${name}: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

/**
 * Create a new document.
 */
export async function createDoc(doctype, values) {
  const response = await fetch(`/api/resource/${doctype}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body: JSON.stringify(values),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.exc || `Failed to create ${doctype}: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

/**
 * Update a document.
 */
export async function updateDoc(doctype, name, values) {
  const response = await fetch(`/api/resource/${doctype}/${name}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || '',
    },
    body: JSON.stringify(values),
  })

  if (!response.ok) {
    throw new Error(`Failed to update ${doctype}/${name}: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

/**
 * Set a single field on a doc via Frappe's set_value RPC.
 */
export async function setValue(doctype, name, fieldname, value) {
  return call('frappe.client.set_value', { doctype, name, fieldname, value })
}

/**
 * Soft-delete a record. CRM Lead/Deal use status='Cancelled'; Contact uses archived flag.
 * Never hard-deletes — preserves history.
 */
export async function softDelete(doctype, name) {
  if (doctype === 'Contact') {
    return setValue(doctype, name, 'archived', 1)
  }
  return setValue(doctype, name, 'status', 'Cancelled')
}
