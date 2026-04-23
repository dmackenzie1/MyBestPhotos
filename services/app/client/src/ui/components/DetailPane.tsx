import type { LabelPatch, PhotoDetail } from "@mybestphotos/shared";
import { formatMetric } from "../lib/utils";
import "../styles/detail-pane.css";

type DetailPaneProps = {
  detail: PhotoDetail | null;
  selectedTags: string[];
  apiBase: string;
  onPatchLabels: (payload: LabelPatch) => Promise<void>;
  notesDraft: string;
  onNotesChange: (notes: string) => void;
  onSaveNotes: () => Promise<void>;
};

export function DetailPane({
  detail,
  selectedTags,
  apiBase,
  onPatchLabels,
  notesDraft,
  onNotesChange,
  onSaveNotes,
}: DetailPaneProps) {
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
            <div><span>Source file</span><strong>{detail.sourceRoot}/{detail.relativePath}</strong></div>
            <div><span>Extension</span><strong>{detail.extension || "--"}</strong></div>
          </div>

          <div className="chip-row">
            <span className="chip">Aesthetic {formatMetric(detail.metrics.aestheticScore)}</span>
            <span className="chip">Print 12x18 {formatMetric(detail.metrics.printScore12x18)}</span>
            <span className="chip">Curation {formatMetric(detail.metrics.curationScore)}</span>
            <span className="chip">Sharpness {formatMetric(1 - (detail.metrics.blurScore ?? 0))}</span>
            <span className="chip">Exposure {formatMetric(detail.metrics.brightnessScore)}</span>
            <span className="chip">Contrast {formatMetric(detail.metrics.contrastScore)}</span>
            <span className="chip">Noise {formatMetric(detail.metrics.noiseScore)}</span>
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
            <button onClick={() => void onPatchLabels({ printCandidate6x8: !(detail.labels.printCandidate6x8 ?? false) })}>6x8</button>
            <button onClick={() => void onPatchLabels({ printCandidate8x10: !(detail.labels.printCandidate8x10 ?? false) })}>8x10</button>
            <button onClick={() => void onPatchLabels({ printCandidate12x18: !(detail.labels.printCandidate12x18 ?? false) })}>12x18</button>
          </div>

          <div className="notes-block">
            <textarea
              placeholder="Notes"
              value={notesDraft}
              onChange={(event) => onNotesChange(event.target.value)}
            />
            <button onClick={() => void onSaveNotes()}>Save Notes</button>
          </div>
        </>
      ) : (
        <p>No photos match these filters. Clear filters or search to see results.</p>
      )}
    </section>
  );
}
