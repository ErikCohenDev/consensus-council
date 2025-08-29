import { useUIState, useAppActions } from '@/stores/appStore'

export const SettingsPage = () => {
  const { theme } = useUIState()
  const { setTheme } = useAppActions()

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Settings</h1>
      <div className="border rounded p-3 space-y-2">
        <div className="font-medium">Theme</div>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as any)}
          className="border rounded px-2 py-1 bg-transparent"
        >
          <option value="auto">Auto</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
    </div>
  )
}

