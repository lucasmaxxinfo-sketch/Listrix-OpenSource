import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Downscale + re-encode an image file before it is stored or sent to AI vision.
// A raw 5MB phone photo becomes ~6.7MB of base64 — some providers count that as
// ~1.6M tokens and reject the request with a context-length error. Compressed to
// ~1024px it stays small enough for any model.
export async function compressImage(file, { maxDim = 1024, quality = 0.78, maxDataUrlChars = 1_500_000 } = {}) {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error("Could not read the image file."));
      el.src = url;
    });
    const scale = Math.min(1, maxDim / Math.max(img.naturalWidth, img.naturalHeight));
    const w = Math.max(1, Math.round(img.naturalWidth * scale));
    const h = Math.max(1, Math.round(img.naturalHeight * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(img, 0, 0, w, h);
    for (const q of [quality, 0.5, 0.3]) {
      const dataUrl = canvas.toDataURL("image/jpeg", q);
      if (dataUrl.length <= maxDataUrlChars) return dataUrl;
    }
    const last = canvas.toDataURL("image/jpeg", 0.2);
    if (last.length > maxDataUrlChars) {
      throw new Error(`Image is too large after compression (${Math.round(last.length / 1024)}KB). Please use a smaller photo.`);
    }
    return last;
  } finally {
    URL.revokeObjectURL(url);
  }
}
