import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProspectCard from '@/components/cards/ProspectCard.vue'

describe('ProspectCard', () => {
  it('renders LEAD badge for CRM Lead', () => {
    const lead = {
      name: 'CRM-LEAD-1',
      doctype: 'CRM Lead',
      first_name: 'Priya',
      mobile_no: '+91999',
      _badge: 'LEAD',
    }
    const w = mount(ProspectCard, { props: { item: lead } })
    expect(w.text()).toContain('Priya')
    expect(w.text()).toContain('LEAD')
  })

  it('renders DEAL badge with value for CRM Deal', () => {
    const deal = {
      name: 'CRM-DEAL-1',
      doctype: 'CRM Deal',
      organization: 'Sneha Corp',
      deal_value: 8500,
      currency: 'INR',
      status: 'Negotiation',
      _badge: 'DEAL',
    }
    const w = mount(ProspectCard, { props: { item: deal } })
    expect(w.text()).toContain('Sneha Corp')
    expect(w.text()).toContain('DEAL')
    expect(w.text()).toContain('8,500')
  })

  it('emits tap on click with the item', async () => {
    const lead = { name: 'CRM-LEAD-1', doctype: 'CRM Lead', first_name: 'X', _badge: 'LEAD' }
    const w = mount(ProspectCard, { props: { item: lead } })
    await w.trigger('click')
    expect(w.emitted('tap')[0][0]).toEqual(lead)
  })
})
