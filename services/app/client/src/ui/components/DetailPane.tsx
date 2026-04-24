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
          <img src={`${apiBase}/photos/${detail.id}/image?size=full&downloadName=${encodeURIComponent(detail.filename)}`} alt={detail.filename} className="preview" />
          <h3>{detail.filename}</h3>
          <p>{detail.descriptionText || "No description available."}</p>

          <div className="meta-list">
            <div><span>Taken</span><strong>{detail.photoTakenAt ? new Date(detail.photoTakenAt).toLocaleString() : "Unknown"}</strong></div>
            <div><span>Camera</span><strong>{detail.cameraMake || "Unknown"} {detail.cameraModel || ""}</strong></div>
            <div><span>Resolution</span><strong>{detail.width ?? "--"} × {detail.height ?? "--"}</strong></div>
            <div><span>Source file</span><strong className="source-file">{detail.sourceRoot}/{detail.relativePath}</strong></div>
          </div>

          <div className="chip-row">
            <span className="chip">Aesthetic {formatMetric(detail.metrics.aestheticScore)}</span>
            <span className="chip">Wall Art {formatMetric(detail.metrics.wallArtScore)}</span>
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
            <button type="button" onClick={() => void onPatchLabels({ favoriteFlag: !(detail.labels.favoriteFlag ?? false) })}>
              {detail.labels.favoriteFlag ? "Unfavorite" : "Favorite"}
            </button>
            {detail.labels.rejectFlag ? (
              <button type="button" onClick={() => void onPatchLabels({ rejectFlag: false })}>Show in Main</button>
            ) : (
              <button type="button" onClick={() => void onPatchLabels({ rejectFlag: true, keepFlag: false })}>Hide</button>
            )}
            <a className="action-link" href={`${apiBase}/photos/${detail.id}/image?size=full&downloadName=${encodeURIComponent(detail.filename)}`} target="_blank" rel="noreferrer">Open Full</a>
          </div>

          <div className="notes-block">
            <textarea
              placeholder="Notes"
              value={notesDraft}
              onChange={(event) => onNotesChange(event.target.value)}
            />
            <button type="button" onClick={() => void onSaveNotes()}>Save Notes</button>
          </div>
        </>
      ) : (
        <p>No photos match these filters. Clear filters or search to see results.</p>
      )}
    </section>
  );
}
