import type { FacetsResponse } from "../types";
import "../styles/filters-pane.css";

type FiltersPaneProps = {
  isCollapsed: boolean;
  isHovered: boolean;
  status: string;
  category: string;
  cameraMake: string;
  cameraModel: string;
  dateFrom: string;
  dateTo: string;
  dateMin: string;
  dateMax: string;
  minScore: number;
  maxScore: number;
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
  onMaxScoreChange: (value: number) => void;
  onReset: () => void;
  onToggleCollapsed: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
};

export function FiltersPane(props: FiltersPaneProps) {
  const {
    isCollapsed,
    isHovered,
    status,
    category,
    cameraMake,
    cameraModel,
    dateFrom,
    dateTo,
    dateMin,
    dateMax,
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
    maxScore,
    onMaxScoreChange,
    onReset,
    onToggleCollapsed,
    onMouseEnter,
    onMouseLeave,
  } = props;

  const isOpen = !isCollapsed || isHovered;

  return (
    <aside className={`filters panel ${isOpen ? "open" : "collapsed"}`} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
      <div className="section-header">
        <h3>{isOpen ? "Filters" : "F"}</h3>
        <div className="filter-actions">
          {isOpen && <button className="inline-btn" onClick={onReset}>Reset</button>}
          <button className="inline-btn" onClick={onToggleCollapsed}>{isCollapsed ? "Expand" : "Collapse"}</button>
        </div>
      </div>
      {!isOpen ? null : (
        <>
          <label>Status</label>
          <select value={status} onChange={(event) => onStatusChange(event.target.value)}>
            <option value="all">All photos</option>
            <option value="keep">Keep</option>
            <option value="favorite">Favorite</option>
            <option value="reject">Rejected</option>
            <option value="unreviewed">Unreviewed</option>
          </select>

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
          <input
            type="date"
            value={dateFrom}
            min={dateMin || undefined}
            max={dateMax || undefined}
            onChange={(event) => onDateFromChange(event.target.value)}
          />

          <label>Date to</label>
          <input
            type="date"
            value={dateTo}
            min={dateMin || undefined}
            max={dateMax || undefined}
            onChange={(event) => onDateToChange(event.target.value)}
          />

          <label>Print Score (12x18) Range</label>
          <div className="score-block">
            <div className="range-row">
              <input type="range" min={0} max={1} step={0.01} value={minScore} onChange={(event) => onMinScoreChange(Number(event.target.value))} />
              <input type="range" min={0} max={1} step={0.01} value={maxScore} onChange={(event) => onMaxScoreChange(Number(event.target.value))} />
            </div>
            <div className="score-val">Range: {minScore.toFixed(2)} to {maxScore.toFixed(2)}</div>
          </div>

          <div className="topics-wrap">
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
          </div>
        </>
      )}
    </aside>
  );
}
