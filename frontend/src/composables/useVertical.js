import { useVerticalStore } from '@/stores/vertical'
import { storeToRefs } from 'pinia'

export function useVertical() {
  const store = useVerticalStore()
  const {
    config,
    loaded,
    verticalType,
    displayName,
    colorScheme,
    navItems,
    homeComponent,
    visibleModules,
    contactFields,
    leadFields,
    statsConfig,
    terminology,
    fabActions,
    businessName,
  } = storeToRefs(store)

  return {
    config,
    loaded,
    verticalType,
    displayName,
    colorScheme,
    navItems,
    homeComponent,
    visibleModules,
    contactFields,
    leadFields,
    statsConfig,
    terminology,
    fabActions,
    businessName,
    term: store.term,
    isModuleVisible: store.isModuleVisible,
  }
}
