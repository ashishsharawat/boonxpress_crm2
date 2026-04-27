export const PAGE_SIZE = 25
export const TOUCH_MIN_PX = 44
export const DEBOUNCE_MS = 300
export const POLL_INTERVAL_MS = 30000

export const APPOINTMENT_STATUS = {
  CONFIRMED: 'Confirmed',
  PENDING: 'Pending',
  DONE: 'Done',
  CANCELLED: 'Cancelled',
}

export const APPOINTMENT_STATUS_COLORS = {
  Confirmed: 'text-green-600 bg-green-50',
  Pending: 'text-yellow-600 bg-yellow-50',
  Done: 'text-gray-600 bg-gray-50',
  Cancelled: 'text-red-600 bg-red-50',
}

export const HEAT_SCORE_COLORS = {
  Hot: 'text-red-600 bg-red-50',
  Warm: 'text-orange-600 bg-orange-50',
  Cold: 'text-blue-600 bg-blue-50',
}
