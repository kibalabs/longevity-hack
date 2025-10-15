/**
 * Simple in-memory store for pending file uploads.
 * This allows us to pass File objects between pages without blocking navigation.
 */

const pendingUploads = new Map<string, File>();

export const setPendingUpload = (analysisId: string, file: File): void => {
  pendingUploads.set(analysisId, file);
};

export const getPendingUpload = (analysisId: string): File | undefined => {
  return pendingUploads.get(analysisId);
};

export const clearPendingUpload = (analysisId: string): void => {
  pendingUploads.delete(analysisId);
};
