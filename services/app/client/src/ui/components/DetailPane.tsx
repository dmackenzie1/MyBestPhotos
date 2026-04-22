import type { LabelPatch, PhotoDetail } from "@mybestphotos/shared";
import { formatMetric } from "../lib/utils";
import "../styles/detail-pane.css";

type DetailPaneProps = {
  detail: PhotoDetail | null;
  selectedTags: string[];
  apiBase: string;
  onPatchLabels: (payload: LabelPatch) => Promise<void>;
  onNotesChange: (notes: string) => void;
};

export function DetailPane({ detail, selectedTags, apiBase, onPatchLabels, onNotesChange }: DetailPaneProps) {
  return (
    <section className="detail panel">
      {detail ? (
        <>
          <img src={`${apiBase}/photos/${detail.id}/image?size=full`} alt={detail.filename} className="preview" />
          <h3>{detail.filename}</h3>
          <p>{detail.descriptionText || "No description available."}</p>

          <div className="meta-list">
            <div><span>Taken</span><strong>{detail.photoTakenAt ? new Date(detail.photoTakenAt).toLocaleString() : "Unknown"}</strong></div>
            <div><span>Camera</span><strong>{detail.cameraMake || "Unknown"} {detail.cameraModel || ""}</strong></div>
            <div><span>Resolution</span><strong>{detail.width ?? "--"} × {detail.height ?? "--"}</strong></div>
          </div>

          <div className="chip-row">
            <span className="chip">Print 12x18 {formatMetric(detail.metrics.printScore12x18)}</span>
            <span className="chip">Curation {formatMetric(detail.metrics.curationScore)}</span>
            <span className="chip">Sharpness {formatMetric(1 - (detail.metrics.blurScore ?? 0))}</span>
            <span className="chip">Exposure {formatMetric(detail.metrics.brightnessScore)}</span>
          </div>

          {selectedTags.length > 0 && (
            <div className="chip-row">
              {selectedTags.map((tag) => <span className="chip" key={tag}>{tag}</span>)}
            </div>
          )}

          <div className="actions">
            <button onClick={() => void onPatchLabels({ keepFlag: true, rejectFlag: false })}>Keep</button>
            <button onClick={() => void onPatchLabels({ favoriteFlag: !(detail.labels.favoriteFlag ?? false) })}>Favorite</button>
            <button onClick={() => void onPatchLabels({ rejectFlag: true, keepFlag: false })}>Reject</button>
          </div>

          <div className="actions">
            <button onClick={() => void onPatchLabels({ printCandidate6x8: true })}>6x8</button>
            <button onClick={() => void onPatchLabels({ printCandidate8x10: true })}>8x10</button>
            <button onClick={() => void onPatchLabels({ printCandidate12x18: true })}>12x18</button>
          </div>

          <textarea
            placeholder="Notes"
            value={detail.labels.notes || ""}
            onChange={(event) => onNotesChange(event.target.value)}
            onBlur={() => void onPatchLabels({ notes: detail.labels.notes || "" })}
          />
        </>
      ) : (
        <p>No photos match these filters. Clear filters or search to see results.</p>
      )}
    </section>
  );
}
