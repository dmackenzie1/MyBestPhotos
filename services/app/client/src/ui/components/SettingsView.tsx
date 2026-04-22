import type { SettingsState } from "../types";
import "../styles/settings-view.css";

type SettingsViewProps = {
  settings: SettingsState;
  onSettingsChange: (next: SettingsState) => void;
};

export function SettingsView({ settings, onSettingsChange }: SettingsViewProps) {
  return (
    <section className="settings panel">
      <div className="section-header">
        <h2>Settings</h2>
        <span>UI preferences are saved for this browser session.</span>
      </div>
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={settings.showScores}
          onChange={(event) => onSettingsChange({ ...settings, showScores: event.target.checked })}
        />
        <span>Show score badges on photo cards</span>
      </label>
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={settings.compactCards}
          onChange={(event) => onSettingsChange({ ...settings, compactCards: event.target.checked })}
        />
        <span>Use compact cards for denser browsing</span>
      </label>
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={settings.autoplayDetailPreview}
          onChange={(event) => onSettingsChange({ ...settings, autoplayDetailPreview: event.target.checked })}
        />
        <span>Auto-load detail preview when selection changes</span>
      </label>
      <label>
        Grid density
        <select
          value={settings.density}
          onChange={(event) => onSettingsChange({ ...settings, density: event.target.value as SettingsState["density"] })}
        >
          <option value="comfortable">Comfortable</option>
          <option value="compact">Compact</option>
        </select>
      </label>
    </section>
  );
}
