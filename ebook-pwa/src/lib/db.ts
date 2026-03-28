import Dexie, { type EntityTable } from 'dexie';

export interface CapturedImage {
  id?: number;
  blob: Blob;
  timestamp: number;
  pageNumber: number;
}

export const db = new Dexie('eBookPWA') as Dexie & {
  images: EntityTable<CapturedImage, 'id'>;
};

// Schema declaration:
db.version(1).stores({
  images: '++id, pageNumber, timestamp',
});

// Helper functions
export async function addImage(blob: Blob, pageNumber: number) {
  try {
    return await db.images.add({
      blob,
      timestamp: Date.now(),
      pageNumber
    });
  } catch (error) {
    console.error('Failed to add image to IndexedDB:', error);
    throw error;
  }
}

export async function getAllImages() {
  return await db.images.orderBy('pageNumber').toArray();
}

export async function clearImages() {
  return await db.images.clear();
}
