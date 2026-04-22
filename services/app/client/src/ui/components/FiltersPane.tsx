import type { FacetsResponse } from "../types";
import "../styles/filters-pane.css";

type FiltersPaneProps = {
  status: string;
  category: string;
  cameraMake: string;
  cameraModel: string;
  dateFrom: string;
  dateTo: string;
  minScore: number;
  facets: FacetsResponse;
  cameraMakeOptions: string[];
  cameraModelOptions: string[];
  onStatusChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onCameraMakeChange: (value: string) => void;
  onCameraModelChange: (value: string) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onMinScoreChange: (value: number) => void;
  onReset: () => void;
};

export function FiltersPane(props: FiltersPaneProps) {
  const {
    status,
    category,
    cameraMake,
    cameraModel,
    dateFrom,
    dateTo,
    minScore,
    facets,
    cameraMakeOptions,
    cameraModelOptions,
    onStatusChange,
    onCategoryChange,
    onCameraMakeChange,
    onCameraModelChange,
    onDateFromChange,
    onDateToChange,
    onMinScoreChange,
    onReset,
  } = props;

  return (
    <aside className="filters panel">
      <div className="section-header">
        <h3>Filters</h3>
        <button className="inline-btn" onClick={onReset}>Reset</button>
      </div>

      <label>Status</label>
      <select value={status} onChange={(event) => onStatusChange(event.target.value)}>
        <option value="all">All photos</option>
        <option value="keep">Keep</option>
        <option value="favorite">Favorite</option>
        <option value="reject">Rejected</option>
        <option value="unreviewed">Unreviewed</option>
      </select>

      <label>Topics / categories</label>
      <div className="topics">
        {(facets.categories || []).map((row) => (
          <button
            key={row.category}
            className={`topic-chip ${category === row.category ? "active" : ""}`}
            onClick={() => onCategoryChange(category === row.category ? "" : row.category)}
          >
            <span>{row.category}</span>
            <strong>{row.count}</strong>
          </button>
        ))}
      </div>

      <label>Camera Make</label>
      <select value={cameraMake} onChange={(event) => onCameraMakeChange(event.target.value)}>
        <option value="">Any camera make</option>
        {cameraMakeOptions.map((value) => (
          <option key={value} value={value}>{value}</option>
        ))}
      </select>

      <label>Camera Model</label>
      <select value={cameraModel} onChange={(event) => onCameraModelChange(event.target.value)}>
        <option value="">Any camera model</option>
        {cameraModelOptions.map((value) => (
          <option key={value} value={value}>{value}</option>
        ))}
      </select>

      <label>Date from</label>
      <input type="date" value={dateFrom} onChange={(event) => onDateFromChange(event.target.value)} />

      <label>Date to</label>
      <input type="date" value={dateTo} onChange={(event) => onDateToChange(event.target.value)} />

      <label>Min Print Score (12x18)</label>
      <input type="range" min={0.5} max={1} step={0.01} value={minScore} onChange={(event) => onMinScoreChange(Number(event.target.value))} />
      <div className="score-val">{minScore.toFixed(2)} - 1.00</div>
    </aside>
  );
}
