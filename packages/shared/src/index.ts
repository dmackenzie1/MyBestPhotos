export type LabelPatch = {
  favoriteFlag?: boolean | null;
  notes?: string | null;
};

export type PhotoListItem = {
  id: number;
  sourceRoot: string;
  relativePath: string;
  filename: string;
  photoTakenAt: string | null;
  cameraMake: string | null;
  cameraModel: string | null;
  curationScore: number | null;
  aestheticScore: number | null;
  wallArtScore: number | null;
  descriptionText: string | null;
  favoriteFlag: boolean | null;
};

export type PhotoDetail = {
  id: number;
  sourceRoot: string;
  relativePath: string;
  filename: string;
  extension: string;
  width: number | null;
  height: number | null;
  photoTakenAt: string | null;
  photoTakenAtSource: string;
  cameraMake: string | null;
  cameraModel: string | null;
  descriptionText: string | null;
  descriptionJson: Record<string, unknown> | null;
  metrics: {
    blurScore: number | null;
    brightnessScore: number | null;
    contrastScore: number | null;
    entropyScore: number | null;
    noiseScore: number | null;
    technicalQualityScore: number | null;
    semanticRelevanceScore: number | null;
    curationScore: number | null;
    aestheticScore: number | null;
    wallArtScore: number | null;
  };
  labels: {
    favoriteFlag: boolean | null;
    notes: string | null;
  };
};
