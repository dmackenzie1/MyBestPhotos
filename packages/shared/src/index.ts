export type LabelPatch = {
  keepFlag?: boolean | null;
  rejectFlag?: boolean | null;
  favoriteFlag?: boolean | null;
  printCandidate6x8?: boolean | null;
  printCandidate8x10?: boolean | null;
  printCandidate12x18?: boolean | null;
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
  printScore12x18: number | null;
  printScore8x10: number | null;
  printScore6x8: number | null;
  curationScore: number | null;
  aestheticScore: number | null;
  descriptionText: string | null;
  keepFlag: boolean | null;
  rejectFlag: boolean | null;
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
    printScore6x8: number | null;
    printScore8x10: number | null;
    printScore12x18: number | null;
  };
  labels: {
    keepFlag: boolean | null;
    rejectFlag: boolean | null;
    favoriteFlag: boolean | null;
    printCandidate6x8: boolean | null;
    printCandidate8x10: boolean | null;
    printCandidate12x18: boolean | null;
    notes: string | null;
  };
};
