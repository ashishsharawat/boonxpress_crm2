import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StageStepper from '@/components/deals/StageStepper.vue'

const stages = ['Qualification', 'Demo', 'Proposal', 'Negotiation']

describe('StageStepper', () => {
  it('renders all stages', () => {
    const w = mount(StageStepper, { props: { stages, current: 'Demo' } })
    stages.forEach((s) => expect(w.text()).toContain(s.slice(0, 4)))
  })

  it('emits change event with target stage on tap', async () => {
    const w = mount(StageStepper, { props: { stages, current: 'Qualification' } })
    const proposal = w.find('[data-stage="Proposal"]')
    await proposal.trigger('click')
    expect(w.emitted('change')[0][0]).toBe('Proposal')
  })

  it('highlights current stage with ring', () => {
    const w = mount(StageStepper, { props: { stages, current: 'Negotiation' } })
    const dot = w.find('[data-stage="Negotiation"] span')
    expect(dot.classes().some((c) => c.startsWith('ring'))).toBe(true)
  })
})
