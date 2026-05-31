"use client";

import Image from "next/image";

interface PreviewTableProps {
  data: any[]; // First 5 rows of data
}

export default function PreviewTable({ data }: PreviewTableProps) {
  if (!data || data.length === 0) return null;

  // Dynamically discover columns from data keys
  const allKeys = Object.keys(data[0]);
  // Put image path fields at the end or hide raw absolute paths to look cleaner
  const displayKeys = allKeys.filter(
    (k) => !["local_image_path", "image", "img", "image_url", "src"].includes(k.toLowerCase())
  );
  
  // Check if any row has a local image path
  const hasLocalImages = data.some(
    (row) => row.local_image_path || row.image || row.image_url
  );

  return (
    <div className="backdrop-blur-md bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 shadow-2xl space-y-4">
      <div>
        <h3 className="text-lg font-bold text-white">Extracted Records Preview</h3>
        <p className="text-xs text-zinc-500 mt-0.5">Showing first {data.length} records matching your instructions</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/60 max-w-full">
        <table className="w-full text-left text-sm text-zinc-300 border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/50 text-zinc-400 font-medium">
              {hasLocalImages && (
                <th className="py-3.5 px-4 font-semibold text-xs uppercase tracking-wider text-center w-24">
                  Photo
                </th>
              )}
              {displayKeys.map((key) => (
                <th
                  key={key}
                  className="py-3.5 px-4 font-semibold text-xs uppercase tracking-wider min-w-[120px]"
                >
                  {String(key).replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {data.map((row, rIdx) => {
              // Extract local image or web image
              const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
              const imgLoc = row.local_image_path 
                ? `${apiBase}/${row.local_image_path}`
                : (row.image || row.image_url || row.img || row.src);

              return (
                <tr
                  key={rIdx}
                  className="hover:bg-zinc-900/30 transition duration-150"
                >
                  {hasLocalImages && (
                    <td className="py-3 px-4 align-middle text-center">
                      {imgLoc ? (
                        <div className="relative w-12 h-12 rounded-lg overflow-hidden border border-zinc-800 bg-zinc-950 inline-block">
                          <Image
                            src={imgLoc}
                            alt="Product preview"
                            fill
                            sizes="48px"
                            className="object-cover"
                            loading="lazy"
                            unoptimized={true} // Bypasses optimization constraints for dynamic user scrapers while keeping loading & styling features intact
                          />
                        </div>
                      ) : (
                        <div className="w-12 h-12 rounded-lg border border-dashed border-zinc-800 bg-zinc-900/10 flex items-center justify-center text-[10px] text-zinc-600 inline-block font-semibold">
                          No Pic
                        </div>
                      )}
                    </td>
                  )}
                  {displayKeys.map((key) => {
                    const cellVal = row[key];
                    let displayVal = "";
                    
                    if (cellVal === null || cellVal === undefined) {
                      displayVal = "-";
                    } else if (typeof cellVal === "object") {
                      displayVal = JSON.stringify(cellVal);
                    } else {
                      displayVal = String(cellVal);
                    }

                    return (
                      <td
                        key={key}
                        className="py-3.5 px-4 align-middle text-zinc-300 font-normal break-words max-w-[250px]"
                      >
                        {displayVal}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
