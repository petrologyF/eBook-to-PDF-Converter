import { useState } from 'react';
import jsPDF from 'jspdf';
import { getAllImages } from '@/lib/db';

export function usePdfGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);

  const generatePdf = async (filename: string, chapter: string) => {
    setIsGenerating(true);
    try {
      const images = await getAllImages();
      if (images.length === 0) {
        alert("No images to convert.");
        setIsGenerating(false);
        return;
      }

      // We assume the first image dictates the PDF size, or A4
      // We will create a PDF that fits the image dimensions
      let pdf: jsPDF | null = null;

      for (let i = 0; i < images.length; i++) {
        const { blob } = images[i];
        
        // Convert Blob to Data URL
        const dataUrl = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.readAsDataURL(blob);
        });

        // Get Image dimensions
        const img = new Image();
        img.src = dataUrl;
        await new Promise((resolve) => { img.onload = resolve; });

        const width = img.width;
        const height = img.height;

        // Initialize PDF with the dimensions of the first image
        if (i === 0) {
          const orientation = width > height ? 'l' : 'p';
          pdf = new jsPDF({
            orientation,
            unit: 'px',
            format: [width, height],
          });
        } else if (pdf) {
          const orientation = width > height ? 'l' : 'p';
          pdf.addPage([width, height], orientation);
        }

        if (pdf) {
          pdf.addImage(dataUrl, 'PNG', 0, 0, width, height);
        }
      }

      if (pdf) {
        const outName = `${filename || 'book'}_${chapter || '01'}.pdf`;
        pdf.save(outName);
        
        // Optional: clear DB after successful creation? 
        // We leave it up to the user via manual clear to avoid losing data by mistake.
      }
      
    } catch (err) {
      console.error("Error generating PDF:", err);
      alert("Failed to generate PDF.");
    } finally {
      setIsGenerating(false);
    }
  };

  return { generatePdf, isGenerating };
}
