import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SegmentPills from '@/components/common/SegmentPills.vue'

const segments = [
  { key: 'a', label: 'A', count: 12 },
  { key: 'b', label: 'B', count: 4 },
]

describe('SegmentPills', () => {
  it('renders all segments with counts', () => {
    const w = mount(SegmentPills, { props: { segments, modelValue: 'a' } })
    expect(w.text()).toContain('A')
    expect(w.text()).toContain('12')
    expect(w.text()).toContain('B')
    expect(w.text()).toContain('4')
  })

  it('emits update:modelValue on click', async () => {
    const w = mount(SegmentPills, { props: { segments, modelValue: 'a' } })
    await w.findAll('button')[1].trigger('click')
    expect(w.emitted('update:modelValue')[0][0]).toBe('b')
  })

  it('marks active pill with primary background', () => {
    const w = mount(SegmentPills, { props: { segments, modelValue: 'b' } })
    const buttons = w.findAll('button')
    expect(buttons[0].classes()).not.toContain('bg-boon-primary')
    expect(buttons[1].classes()).toContain('bg-boon-primary')
  })
})
